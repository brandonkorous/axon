"""VaultVectorStore — per-agent LanceDB vector index for semantic search.

Stores embeddings alongside metadata (path, name, memory_tier) in a
LanceDB table at ``{vault_path}/.lancedb/``.  All LanceDB operations
are sync and run via ``asyncio.to_thread`` to stay async-friendly.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from axon.logging import get_logger
from axon.vault.embeddings import EmbeddingClient

logger = get_logger(__name__)

TABLE_NAME = "vault_vectors"


class VaultVectorStore:
    """Manage a per-agent LanceDB vector table."""

    def __init__(
        self,
        vault_path: Path | str,
        embedding_client: EmbeddingClient,
        dimensions: int = 384,
    ) -> None:
        self._vault_path = Path(vault_path)
        self._db_path = self._vault_path / ".lancedb"
        self._embedding_client = embedding_client
        self._dimensions = dimensions
        self._db: Any = None  # lancedb.DBConnection (lazy)

    # ── Public API ──────────────────────────────────────────────────

    async def upsert(
        self, path: str, name: str, memory_tier: str, text: str,
    ) -> None:
        """Embed *text* and upsert the entry into the vector table."""
        if not text.strip():
            return
        vector = await self._embedding_client.embed_one(text)
        await asyncio.to_thread(
            self._upsert_sync, path, name, memory_tier, text, vector,
        )

    async def remove(self, path: str) -> None:
        """Remove a single entry by vault path."""
        await asyncio.to_thread(self._remove_sync, path)

    async def search(
        self,
        query: str,
        limit: int = 10,
        memory_tier: str | None = None,
    ) -> list[dict[str, Any]]:
        """Semantic search — returns ranked results with distance scores."""
        vector = await self._embedding_client.embed_one(query)
        return await asyncio.to_thread(
            self._search_sync, vector, limit, memory_tier,
        )

    async def rebuild(self, vault: Any) -> int:
        """Full reindex — scan all vault ``.md`` files and upsert vectors.

        *vault* must be a :class:`VaultManager` instance.
        Returns the number of files indexed.
        """
        entries = await asyncio.to_thread(self._collect_entries, vault)
        if not entries:
            return 0

        texts = [e["text"] for e in entries]
        vectors = await self._embedding_client.embed(texts)

        for entry, vec in zip(entries, vectors):
            entry["vector"] = vec

        await asyncio.to_thread(self._rebuild_sync, entries)
        logger.info("vector_rebuild_complete", count=len(entries))
        return len(entries)

    # ── Sync internals (run via to_thread) ──────────────────────────

    def _get_db(self) -> Any:
        if self._db is None:
            import lancedb

            self._db_path.mkdir(parents=True, exist_ok=True)
            self._db = lancedb.connect(str(self._db_path))
        return self._db

    def _ensure_table(self) -> Any:
        """Return the table, creating it if it doesn't exist."""
        import pyarrow as pa

        db = self._get_db()
        try:
            return db.open_table(TABLE_NAME)
        except Exception:
            schema = pa.schema([
                pa.field("path", pa.utf8()),
                pa.field("name", pa.utf8()),
                pa.field("memory_tier", pa.utf8()),
                pa.field("text", pa.utf8()),
                pa.field("vector", pa.list_(pa.float32(), self._dimensions)),
            ])
            return db.create_table(TABLE_NAME, schema=schema)

    def _upsert_sync(
        self,
        path: str,
        name: str,
        memory_tier: str,
        text: str,
        vector: list[float],
    ) -> None:
        table = self._ensure_table()
        # Remove existing entry for this path (if any)
        try:
            table.delete(f"path = '{path}'")
        except Exception:
            pass
        table.add([{
            "path": path,
            "name": name,
            "memory_tier": memory_tier,
            "text": text,
            "vector": vector,
        }])

    def _remove_sync(self, path: str) -> None:
        try:
            table = self._ensure_table()
            table.delete(f"path = '{path}'")
        except Exception:
            pass

    def _search_sync(
        self,
        vector: list[float],
        limit: int,
        memory_tier: str | None,
    ) -> list[dict[str, Any]]:
        try:
            table = self._ensure_table()
        except Exception:
            return []

        query = table.search(vector).limit(limit)
        if memory_tier:
            query = query.where(f"memory_tier = '{memory_tier}'")

        try:
            results = query.to_pandas()
        except Exception:
            return []

        return [
            {
                "path": row["path"],
                "name": row["name"],
                "memory_tier": row["memory_tier"],
                "text": row["text"][:200],
                "score": float(row.get("_distance", 0)),
            }
            for _, row in results.iterrows()
        ]

    def _collect_entries(self, vault: Any) -> list[dict[str, Any]]:
        """Walk vault markdown files and extract text for embedding."""
        entries: list[dict[str, Any]] = []
        vault_path = Path(vault.vault_path)

        for md_file in vault_path.rglob("*.md"):
            rel = md_file.relative_to(vault_path).as_posix()
            # Skip hidden dirs, conversations archive, deep memories
            if rel.startswith(".") or rel.startswith("conversations/"):
                continue
            try:
                content = md_file.read_text(encoding="utf-8")
            except Exception:
                continue
            if not content.strip():
                continue

            # Extract metadata from frontmatter if present
            name = md_file.stem
            memory_tier = ""
            if rel.startswith("memory/short-term"):
                memory_tier = "short_term"
            elif rel.startswith("memory/long-term"):
                memory_tier = "long_term"
            elif rel.startswith("deep/"):
                memory_tier = "deep"

            # Use first 1000 chars for embedding (balance quality vs cost)
            text = content[:1000]
            entries.append({
                "path": rel,
                "name": name,
                "memory_tier": memory_tier,
                "text": text,
            })

        return entries

    def _rebuild_sync(self, entries: list[dict[str, Any]]) -> None:
        """Drop and recreate the table with all entries."""
        import pyarrow as pa

        db = self._get_db()
        # Drop existing table
        try:
            db.drop_table(TABLE_NAME)
        except Exception:
            pass

        schema = pa.schema([
            pa.field("path", pa.utf8()),
            pa.field("name", pa.utf8()),
            pa.field("memory_tier", pa.utf8()),
            pa.field("text", pa.utf8()),
            pa.field("vector", pa.list_(pa.float32(), self._dimensions)),
        ])
        db.create_table(TABLE_NAME, data=entries, schema=schema)

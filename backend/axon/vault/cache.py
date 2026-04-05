"""VaultCache — in-memory cache of all vault files for fast search and graph building."""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from axon.logging import get_logger
from axon.vault.frontmatter import parse_frontmatter
from axon.vault.wikilinks import extract_wikilinks, resolve_wikilink

logger = get_logger(__name__)


@dataclass
class CachedFile:
    """A single cached vault file with parsed metadata."""

    path: str  # Relative path from vault root
    metadata: dict[str, Any]  # Parsed YAML frontmatter
    body: str  # Markdown body (without frontmatter)
    raw: str  # Full raw content (frontmatter + body)
    links: list[str] = field(default_factory=list)  # Resolved outbound wikilink paths
    backlinks: list[str] = field(default_factory=list)  # Computed inbound link paths
    mtime: float = 0.0  # os.path.getmtime for staleness check


class VaultCache:
    """In-memory cache of all markdown files in a vault.

    Thread-safe — uses a lock for mutations so the file watcher
    can update the cache from a background thread.
    """

    def __init__(self, vault_path: str | Path):
        self.vault_path = Path(vault_path)
        self._files: dict[str, CachedFile] = {}
        self._lock = threading.Lock()

    @property
    def files(self) -> dict[str, CachedFile]:
        return self._files

    def load_all(self) -> None:
        """Hydrate the cache by reading all .md files from disk."""
        # First pass: collect all .md files and build a filename index
        # so resolve_wikilink never needs to rglob per-link.
        all_md_files: list[tuple[Path, str]] = []
        filename_index: dict[str, list[Path]] = {}

        for md_file in self.vault_path.rglob("*.md"):
            if md_file.name.startswith("."):
                continue
            rel_path = str(md_file.relative_to(self.vault_path)).replace("\\", "/")
            all_md_files.append((md_file, rel_path))
            filename_index.setdefault(md_file.name, []).append(md_file)

        # Second pass: parse files using the pre-built index
        files: dict[str, CachedFile] = {}
        for md_file, rel_path in all_md_files:
            try:
                cached = self._parse_file(md_file, rel_path, filename_index)
                if cached:
                    files[rel_path] = cached
            except Exception:
                logger.warning("Failed to cache: %s", md_file, exc_info=True)

        with self._lock:
            self._files = files
            self._recompute_backlinks()

        logger.info("VaultCache loaded %d files from %s", len(self._files), self.vault_path)

    def get(self, path: str) -> CachedFile | None:
        """Get a cached file by relative path."""
        return self._files.get(path)

    def update(self, path: str) -> None:
        """Re-read a single file from disk and update the cache."""
        full_path = self.vault_path / path
        if not full_path.exists():
            self.remove(path)
            return

        cached = self._parse_file(full_path, path)
        if not cached:
            return

        with self._lock:
            self._files[path] = cached
            self._recompute_backlinks()

    def remove(self, path: str) -> None:
        """Remove a file from the cache."""
        with self._lock:
            self._files.pop(path, None)
            self._recompute_backlinks()

    def search(self, query: str, max_results: int = 20) -> list[dict[str, Any]]:
        """Full-text search across cached files.

        Uses in-memory scan. For FTS5-powered search, use
        search_fts() from axon.db.crud.vault_index with the agent's DB session.
        """
        results: list[dict[str, Any]] = []
        query_lower = query.lower()

        for rel_path, cached in self._files.items():
            if query_lower in cached.raw.lower():
                idx = cached.raw.lower().index(query_lower)
                start = max(0, idx - 100)
                end = min(len(cached.raw), idx + len(query) + 100)
                snippet = cached.raw[start:end].strip()

                results.append({
                    "path": rel_path,
                    "title": cached.metadata.get("name", Path(rel_path).stem),
                    "snippet": snippet,
                })

                if len(results) >= max_results:
                    break

        return results

    def list_branch(self, branch: str) -> list[dict[str, Any]]:
        """List all files in a branch from cache."""
        files: list[dict[str, Any]] = []

        for rel_path, cached in sorted(self._files.items()):
            parts = rel_path.split("/")
            if len(parts) > 1 and parts[0] == branch:
                files.append({
                    "path": rel_path,
                    "name": Path(rel_path).stem,
                    "title": cached.metadata.get("name", Path(rel_path).stem),
                    "description": cached.metadata.get("description", ""),
                })

        return files

    def build_graph(self) -> "VaultGraph":
        """Derive a VaultGraph from cached files (no disk I/O)."""
        from axon.vault.graph import GraphEdge, GraphNode, VaultGraph

        nodes: dict[str, GraphNode] = {}
        edges: list[GraphEdge] = []
        adjacency: dict[str, list[str]] = {}
        backlinks: dict[str, list[str]] = {}

        # Build filename index from cached files to avoid rglob
        filename_index: dict[str, list[Path]] = {}
        for rel_path in self._files:
            full = self.vault_path / rel_path
            filename_index.setdefault(full.name, []).append(full)

        # Build nodes from cache
        for rel_path, cached in self._files.items():
            parts = rel_path.split("/")
            branch = parts[0] if len(parts) > 1 else ""

            raw_tags = cached.metadata.get("tags", "")
            if isinstance(raw_tags, str):
                tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
            elif isinstance(raw_tags, list):
                tags = raw_tags
            else:
                tags = []

            nodes[rel_path] = GraphNode(
                path=rel_path,
                name=Path(rel_path).stem,
                branch=branch,
                title=cached.metadata.get("name", Path(rel_path).stem),
                description=cached.metadata.get("description", ""),
                tags=tags,
            )
            adjacency[rel_path] = []
            backlinks[rel_path] = []

        # Build edges from cached links
        for rel_path, cached in self._files.items():
            wikilinks = extract_wikilinks(cached.raw)
            for link in wikilinks:
                resolved = resolve_wikilink(
                    link.target, self.vault_path, self.vault_path / rel_path,
                    filename_index,
                )
                if resolved and resolved.exists():
                    target_path = str(resolved.relative_to(self.vault_path)).replace("\\", "/")
                    if target_path in nodes:
                        edges.append(GraphEdge(
                            source=rel_path,
                            target=target_path,
                            context=link.context,
                            line_number=link.line_number,
                        ))
                        adjacency[rel_path].append(target_path)
                        backlinks.setdefault(target_path, []).append(rel_path)

            nodes[rel_path].link_count = len(adjacency.get(rel_path, []))

        for path, bl in backlinks.items():
            if path in nodes:
                nodes[path].backlink_count = len(bl)

        return VaultGraph(nodes=nodes, edges=edges, adjacency=adjacency, backlinks=backlinks)

    # ── Internal ──────────────────────────────────────────────────────

    def _parse_file(
        self,
        full_path: Path,
        rel_path: str,
        filename_index: dict[str, list[Path]] | None = None,
    ) -> CachedFile | None:
        """Parse a single file into a CachedFile."""
        try:
            raw = full_path.read_text(encoding="utf-8")
        except Exception:
            return None

        try:
            metadata, body = parse_frontmatter(raw)
        except Exception:
            metadata, body = {}, raw

        # Resolve outbound wikilinks
        links: list[str] = []
        for wl in extract_wikilinks(raw):
            resolved = resolve_wikilink(
                wl.target, self.vault_path, full_path, filename_index,
            )
            if resolved and resolved.exists():
                target = str(resolved.relative_to(self.vault_path)).replace("\\", "/")
                links.append(target)

        return CachedFile(
            path=rel_path,
            metadata=metadata,
            body=body,
            raw=raw,
            links=links,
            mtime=os.path.getmtime(full_path),
        )

    def _recompute_backlinks(self) -> None:
        """Recompute all backlinks from cached link data."""
        # Clear existing backlinks
        for cached in self._files.values():
            cached.backlinks = []

        # Rebuild from links
        for rel_path, cached in self._files.items():
            for target in cached.links:
                target_file = self._files.get(target)
                if target_file:
                    target_file.backlinks.append(rel_path)

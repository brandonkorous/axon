"""CRUD operations for the per-agent vault index (agent.db).

Handles vault_entry + vault_link tables, FTS5 search, and full index rebuild.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from axon.db.agent_models import ConfidenceHistory, VaultEntry, VaultLink
from axon.vault.frontmatter import parse_frontmatter

logger = logging.getLogger(__name__)

CONTENT_PREVIEW_CHARS = 500


async def upsert_entry(session: AsyncSession, entry: dict[str, Any]) -> None:
    """Insert or update a vault_entry row."""
    existing = await session.get(VaultEntry, entry["path"])
    if existing:
        for key, value in entry.items():
            if key != "path":
                setattr(existing, key, value)
    else:
        session.add(VaultEntry(**entry))
    await session.commit()


async def remove_entry(session: AsyncSession, path: str) -> None:
    """Remove a vault entry and its links."""
    await session.execute(delete(VaultEntry).where(VaultEntry.path == path))
    await session.execute(delete(VaultLink).where(VaultLink.source_path == path))
    await session.execute(delete(VaultLink).where(VaultLink.target_path == path))
    await session.commit()


async def set_links(
    session: AsyncSession, source_path: str, targets: list[str],
) -> None:
    """Replace all outbound links for a source file."""
    await session.execute(
        delete(VaultLink).where(VaultLink.source_path == source_path),
    )
    for target in targets:
        session.add(VaultLink(source_path=source_path, target_path=target))
    await session.commit()


async def search_fts(
    session: AsyncSession, query: str, limit: int = 20,
) -> list[dict[str, Any]]:
    """Full-text search across vault entries via FTS5.

    Returns list of {path, name, description, tags, confidence, rank}.
    """
    # FTS5 match syntax — quote the query to handle special chars
    safe_query = query.replace('"', '""')
    sql = text("""
        SELECT ve.path, ve.name, ve.description, ve.tags, ve.confidence,
               ve.content_preview, ve.link_count, ve.backlink_count,
               rank
        FROM vault_entry_fts
        JOIN vault_entry ve ON vault_entry_fts.rowid = ve.rowid
        WHERE vault_entry_fts MATCH :query
        ORDER BY rank
        LIMIT :limit
    """)
    result = await session.execute(sql, {"query": safe_query, "limit": limit})
    return [
        {
            "path": row[0], "name": row[1], "description": row[2],
            "tags": row[3], "confidence": row[4], "content_preview": row[5],
            "link_count": row[6], "backlink_count": row[7], "rank": row[8],
        }
        for row in result.fetchall()
    ]


async def get_links(session: AsyncSession, path: str) -> list[str]:
    """Get outbound link targets for a file."""
    result = await session.execute(
        select(VaultLink.target_path).where(VaultLink.source_path == path),
    )
    return [row[0] for row in result.fetchall()]


async def get_backlinks(session: AsyncSession, path: str) -> list[str]:
    """Get inbound link sources for a file."""
    result = await session.execute(
        select(VaultLink.source_path).where(VaultLink.target_path == path),
    )
    return [row[0] for row in result.fetchall()]


async def add_confidence_event(
    session: AsyncSession, file_path: str, date: str, value: float, reason: str,
) -> None:
    """Record a confidence change event."""
    session.add(ConfidenceHistory(
        file_path=file_path, date=date, value=value, reason=reason,
    ))
    await session.commit()


async def rebuild_index(
    session: AsyncSession, vault_path: str | Path,
) -> int:
    """Full rebuild — scan vault .md files and populate agent.db.

    Returns number of files indexed.
    """
    from axon.vault.wikilinks import extract_wikilinks, resolve_wikilink

    vault = Path(vault_path)
    count = 0

    # Clear existing data
    await session.execute(delete(VaultEntry))
    await session.execute(delete(VaultLink))
    await session.commit()

    for md_file in vault.rglob("*.md"):
        if md_file.name.startswith("."):
            continue
        try:
            rel_path = str(md_file.relative_to(vault)).replace("\\", "/")
            raw = md_file.read_text(encoding="utf-8")
            metadata, body = parse_frontmatter(raw)

            entry = _metadata_to_entry(rel_path, metadata, body)
            session.add(VaultEntry(**entry))

            # Extract and store links
            links = extract_wikilinks(raw)
            for link in links:
                resolved = resolve_wikilink(link.target, vault, md_file)
                if resolved and resolved.exists():
                    target = str(resolved.relative_to(vault)).replace("\\", "/")
                    session.add(VaultLink(source_path=rel_path, target_path=target))

            count += 1
        except Exception:
            logger.warning("Failed to index: %s", md_file, exc_info=True)

    await session.commit()

    # Update link/backlink counts
    await _recount_links(session)

    logger.info("Vault index rebuilt: %d files from %s", count, vault)
    return count


def _metadata_to_entry(path: str, metadata: dict, body: str) -> dict[str, Any]:
    """Convert parsed frontmatter + body into a vault_entry dict."""
    tags = metadata.get("tags", "")
    if isinstance(tags, list):
        tags = ", ".join(tags)

    return {
        "path": path,
        "name": str(metadata.get("name", Path(path).stem)),
        "description": str(metadata.get("description", "")),
        "type": str(metadata.get("type", "")),
        "tags": str(tags),
        "content_preview": body[:CONTENT_PREVIEW_CHARS],
        "confidence": float(metadata.get("confidence", 0.5)),
        "status": str(metadata.get("status", "active")),
        "learning_type": str(metadata.get("learning_type", "")),
        "date": str(metadata.get("date", "")),
    }


async def _recount_links(session: AsyncSession) -> None:
    """Update link_count and backlink_count on all vault_entry rows."""
    await session.execute(text("""
        UPDATE vault_entry SET link_count = (
            SELECT COUNT(*) FROM vault_link WHERE vault_link.source_path = vault_entry.path
        )
    """))
    await session.execute(text("""
        UPDATE vault_entry SET backlink_count = (
            SELECT COUNT(*) FROM vault_link WHERE vault_link.target_path = vault_entry.path
        )
    """))
    await session.commit()

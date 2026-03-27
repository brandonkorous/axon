"""FTS5 virtual table setup for per-agent vault search.

SQLAlchemy doesn't manage FTS5 tables, so we create them with raw SQL.
These are safe to re-run — CREATE ... IF NOT EXISTS.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Connection


def create_fts_tables(conn: Connection) -> None:
    """Create FTS5 virtual table mirroring vault_entry for full-text search.

    The content table is vault_entry — FTS5 reads from it automatically.
    We index name, description, tags, and content_preview.
    """
    conn.execute(text("""
        CREATE VIRTUAL TABLE IF NOT EXISTS vault_entry_fts
        USING fts5(
            name,
            description,
            tags,
            content_preview,
            content='vault_entry',
            content_rowid='rowid'
        )
    """))

    # Triggers to keep FTS5 in sync with vault_entry changes.
    # SQLite FTS5 content-sync requires manual triggers.
    conn.execute(text("""
        CREATE TRIGGER IF NOT EXISTS vault_entry_ai AFTER INSERT ON vault_entry BEGIN
            INSERT INTO vault_entry_fts(rowid, name, description, tags, content_preview)
            VALUES (new.rowid, new.name, new.description, new.tags, new.content_preview);
        END
    """))

    conn.execute(text("""
        CREATE TRIGGER IF NOT EXISTS vault_entry_ad AFTER DELETE ON vault_entry BEGIN
            INSERT INTO vault_entry_fts(vault_entry_fts, rowid, name, description, tags, content_preview)
            VALUES ('delete', old.rowid, old.name, old.description, old.tags, old.content_preview);
        END
    """))

    conn.execute(text("""
        CREATE TRIGGER IF NOT EXISTS vault_entry_au AFTER UPDATE ON vault_entry BEGIN
            INSERT INTO vault_entry_fts(vault_entry_fts, rowid, name, description, tags, content_preview)
            VALUES ('delete', old.rowid, old.name, old.description, old.tags, old.content_preview);
            INSERT INTO vault_entry_fts(rowid, name, description, tags, content_preview)
            VALUES (new.rowid, new.name, new.description, new.tags, new.content_preview);
        END
    """))

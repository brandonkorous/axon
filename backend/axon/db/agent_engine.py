"""Per-agent SQLite engine manager.

Each agent gets its own agent.db in its vault folder.
Engines are lazily created and cached by vault path.
"""

from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from axon.db.agent_models import AgentBase

logger = logging.getLogger(__name__)

# Cache: vault_path → (engine, session_factory)
_agent_engines: dict[str, tuple[AsyncEngine, async_sessionmaker[AsyncSession]]] = {}


async def init_agent_db(vault_path: str) -> async_sessionmaker[AsyncSession]:
    """Initialize an agent's SQLite database, creating tables if needed.

    Returns the session factory for this agent's DB.
    """
    vault_path = str(Path(vault_path).resolve())

    if vault_path in _agent_engines:
        return _agent_engines[vault_path][1]

    db_path = Path(vault_path) / "agent.db"
    url = f"sqlite+aiosqlite:///{db_path}"

    engine = create_async_engine(
        url,
        echo=False,
        connect_args={"check_same_thread": False},
    )
    factory = async_sessionmaker(engine, expire_on_commit=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(AgentBase.metadata.create_all)

    # Create FTS5 virtual table (not managed by SQLAlchemy)
    from axon.db.agent_fts import create_fts_tables

    async with engine.begin() as conn:
        await conn.run_sync(create_fts_tables)

    _agent_engines[vault_path] = (engine, factory)
    logger.info("Agent DB initialized: %s", db_path)
    return factory


def get_agent_session_factory(vault_path: str) -> async_sessionmaker[AsyncSession] | None:
    """Get the session factory for an agent's DB, or None if not initialized."""
    vault_path = str(Path(vault_path).resolve())
    pair = _agent_engines.get(vault_path)
    return pair[1] if pair else None


async def shutdown_agent_db(vault_path: str) -> None:
    """Dispose a single agent's DB engine."""
    vault_path = str(Path(vault_path).resolve())
    pair = _agent_engines.pop(vault_path, None)
    if pair:
        await pair[0].dispose()


async def shutdown_all_agent_dbs() -> None:
    """Dispose all agent DB engines — call on app shutdown."""
    for vault_path in list(_agent_engines.keys()):
        await shutdown_agent_db(vault_path)
    logger.info("All agent databases closed")

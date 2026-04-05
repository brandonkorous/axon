"""Database engine and session factory — provider-agnostic.

Supports SQLite (default) and Postgres via DATABASE_URL env var.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from axon.logging import get_logger

logger = get_logger(__name__)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _build_url() -> str:
    """Derive database URL from settings."""
    from axon.config import settings

    if settings.database_url:
        return settings.database_url

    # Default: SQLite in the orgs data directory
    orgs = settings.axon_orgs_dir.rstrip("/\\")
    return f"sqlite+aiosqlite:///{orgs}/data/axon.db"


async def init_db() -> None:
    """Create engine, ensure tables exist, make session factory available."""
    global _engine, _session_factory

    url = _build_url()
    is_sqlite = url.startswith("sqlite")

    connect_args = {"check_same_thread": False} if is_sqlite else {}

    _engine = create_async_engine(url, echo=False, connect_args=connect_args)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)

    # Ensure parent directory exists for SQLite
    if is_sqlite:
        db_path = url.split("///", 1)[1]
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    # Create tables (Alembic handles this in production; fallback for dev)
    from axon.db.base import Base

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database initialized: %s", url.split("@")[-1] if "@" in url else url)


async def shutdown_db() -> None:
    """Dispose engine and release connections."""
    global _engine
    if _engine:
        await _engine.dispose()
        logger.info("Database connection closed")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async session — use as a FastAPI Depends."""
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    async with _session_factory() as session:
        yield session

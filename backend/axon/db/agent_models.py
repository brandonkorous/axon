"""SQLAlchemy models for per-agent agent.db.

Each agent has its own SQLite database with these tables.
Separate Base from the central DB so metadata.create_all
only creates agent-scoped tables.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class AgentBase(DeclarativeBase):
    """Base class for agent-scoped models (separate from central DB)."""

    pass


# ── Vault Index ────────────────────────────────────────────────────


class VaultEntry(AgentBase):
    """Indexed mirror of a vault markdown file's metadata."""

    __tablename__ = "vault_entry"

    path: Mapped[str] = mapped_column(String(500), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    type: Mapped[str] = mapped_column(String(50), default="")
    tags: Mapped[str] = mapped_column(Text, default="")
    content_preview: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    status: Mapped[str] = mapped_column(String(20), default="active")
    learning_type: Mapped[str] = mapped_column(String(50), default="")
    date: Mapped[str] = mapped_column(String(20), default="")
    link_count: Mapped[int] = mapped_column(Integer, default=0)
    backlink_count: Mapped[int] = mapped_column(Integer, default=0)
    last_modified: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(),
    )


class VaultLink(AgentBase):
    """A wikilink edge between two vault files."""

    __tablename__ = "vault_link"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_path: Mapped[str] = mapped_column(String(500), index=True)
    target_path: Mapped[str] = mapped_column(String(500), index=True)


# ── Confidence History ─────────────────────────────────────────────


class ConfidenceHistory(AgentBase):
    """A single confidence change event for a vault file."""

    __tablename__ = "confidence_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_path: Mapped[str] = mapped_column(String(500), index=True)
    date: Mapped[str] = mapped_column(String(20))
    value: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(Text, default="")


# ── Conversations ──────────────────────────────────────────────────


class ConversationMessage(AgentBase):
    """A single message in a conversation."""

    __tablename__ = "conversation_message"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(String(100), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[float] = mapped_column(Float)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")


# ── Lifecycle State ────────────────────────────────────────────────


class LifecycleState(AgentBase):
    """Single-row table for agent lifecycle state."""

    __tablename__ = "lifecycle_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    status: Mapped[str] = mapped_column(String(20), default="active")
    strategy_override: Mapped[str | None] = mapped_column(Text, nullable=True)
    rate_limit_json: Mapped[str] = mapped_column(Text, default='{"max_per_minute": 60}')
    paused_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    terminated_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    queued_messages_json: Mapped[str] = mapped_column(Text, default="[]")


# ── Learning State ─────────────────────────────────────────────────


class LearningState(AgentBase):
    """Single-row table for learning pipeline checkpoint."""

    __tablename__ = "learning_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    turn_count: Mapped[int] = mapped_column(Integer, default=0)
    last_consolidation: Mapped[str] = mapped_column(String(30), default="")
    last_decay: Mapped[str] = mapped_column(String(30), default="")

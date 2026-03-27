"""CRUD operations for conversation messages in agent.db."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from axon.db.agent_models import ConversationMessage


async def add_message(
    session: AsyncSession,
    conversation_id: str,
    role: str,
    content: str,
    timestamp: float,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Insert a single message into the conversation."""
    session.add(ConversationMessage(
        conversation_id=conversation_id,
        role=role,
        content=content,
        timestamp=timestamp,
        metadata_json=json.dumps(metadata or {}),
    ))
    await session.commit()


async def get_history(
    session: AsyncSession,
    conversation_id: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Get the most recent messages for a conversation."""
    result = await session.execute(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.timestamp.desc())
        .limit(limit)
    )
    rows = result.scalars().all()
    # Return in chronological order
    return [
        {
            "role": m.role,
            "content": m.content,
            "timestamp": m.timestamp,
            "metadata": json.loads(m.metadata_json) if m.metadata_json else {},
        }
        for m in reversed(rows)
    ]


async def list_conversations(session: AsyncSession) -> list[dict[str, Any]]:
    """List all distinct conversation IDs with message counts."""
    from sqlalchemy import func

    result = await session.execute(
        select(
            ConversationMessage.conversation_id,
            func.count(ConversationMessage.id).label("count"),
            func.max(ConversationMessage.timestamp).label("last_at"),
            func.min(ConversationMessage.timestamp).label("first_at"),
        )
        .group_by(ConversationMessage.conversation_id)
        .order_by(func.max(ConversationMessage.timestamp).desc())
    )
    return [
        {
            "conversation_id": row[0],
            "message_count": row[1],
            "last_message_at": row[2],
            "created_at": row[3],
        }
        for row in result.fetchall()
    ]


async def search_messages(
    session: AsyncSession,
    query: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Search across all conversation messages by content."""
    result = await session.execute(
        select(ConversationMessage)
        .where(ConversationMessage.content.ilike(f"%{query}%"))
        .order_by(ConversationMessage.timestamp.desc())
        .limit(limit)
    )
    return [
        {
            "conversation_id": m.conversation_id,
            "role": m.role,
            "content": m.content,
            "timestamp": m.timestamp,
        }
        for m in result.scalars().all()
    ]


async def delete_conversation(session: AsyncSession, conversation_id: str) -> int:
    """Delete all messages for a conversation. Returns count deleted."""
    result = await session.execute(
        delete(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation_id)
    )
    await session.commit()
    return result.rowcount or 0


async def import_from_json(
    session: AsyncSession,
    conversation_id: str,
    messages: list[dict[str, Any]],
) -> int:
    """Import messages from the legacy JSON format into agent.db."""
    count = 0
    for m in messages:
        session.add(ConversationMessage(
            conversation_id=conversation_id,
            role=m.get("role", "user"),
            content=m.get("content", ""),
            timestamp=m.get("timestamp", 0),
            metadata_json=json.dumps(m.get("metadata", {})),
        ))
        count += 1
    await session.commit()
    return count

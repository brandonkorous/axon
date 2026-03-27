"""CRUD operations for agent lifecycle state in agent.db."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from axon.db.agent_models import LifecycleState


async def get_state(session: AsyncSession) -> dict[str, Any] | None:
    """Get the agent's lifecycle state (single-row table)."""
    result = await session.execute(select(LifecycleState).where(LifecycleState.id == 1))
    row = result.scalar_one_or_none()
    if not row:
        return None
    return {
        "status": row.status,
        "strategy_override": row.strategy_override,
        "rate_limit": json.loads(row.rate_limit_json),
        "paused_at": row.paused_at,
        "terminated_at": row.terminated_at,
        "queued_messages": json.loads(row.queued_messages_json),
    }


async def save_state(
    session: AsyncSession,
    status: str,
    strategy_override: str | None = None,
    rate_limit: dict[str, Any] | None = None,
    paused_at: float | None = None,
    terminated_at: float | None = None,
    queued_messages: list[str] | None = None,
) -> None:
    """Upsert the agent's lifecycle state."""
    result = await session.execute(select(LifecycleState).where(LifecycleState.id == 1))
    row = result.scalar_one_or_none()

    if row:
        row.status = status
        row.strategy_override = strategy_override
        row.rate_limit_json = json.dumps(rate_limit or {"max_per_minute": 60})
        row.paused_at = paused_at
        row.terminated_at = terminated_at
        row.queued_messages_json = json.dumps(queued_messages or [])
    else:
        session.add(LifecycleState(
            id=1,
            status=status,
            strategy_override=strategy_override,
            rate_limit_json=json.dumps(rate_limit or {"max_per_minute": 60}),
            paused_at=paused_at,
            terminated_at=terminated_at,
            queued_messages_json=json.dumps(queued_messages or []),
        ))
    await session.commit()

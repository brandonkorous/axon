"""Calendar routes — unified calendar event aggregation."""

from __future__ import annotations

from fastapi import APIRouter

import axon.registry as registry
from axon.calendar.aggregator import create_default_aggregator

router = APIRouter()
org_router = APIRouter()


async def _get_events(
    org_id: str,
    start: str,
    end: str,
    agent_id: str | None = None,
    source: str | None = None,
):
    source_filter: set[str] | None = None
    if source:
        source_filter = {s.strip() for s in source.split(",")}

    aggregator = create_default_aggregator()
    return await aggregator.get_events(
        org_id, start, end, agent_id, source_filter,
    )


# ── Org-scoped routes ─────────────────────────────────────────────────


@org_router.get("")
async def calendar_events_org(
    org_id: str,
    start: str,
    end: str,
    agent_id: str | None = None,
    source: str | None = None,
):
    return await _get_events(org_id, start, end, agent_id, source)


# ── Legacy routes ─────────────────────────────────────────────────────


@router.get("")
async def calendar_events_legacy(
    start: str,
    end: str,
    agent_id: str | None = None,
    source: str | None = None,
):
    return await _get_events(
        registry.default_org_id, start, end, agent_id, source,
    )

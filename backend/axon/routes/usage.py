"""Usage routes — LLM token and cost analytics."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

import axon.registry as registry

router = APIRouter()
org_router = APIRouter()


def _get_usage_tracker(org_id: str):
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Organization not found: {org_id}")
    if not org.usage_tracker:
        raise HTTPException(404, f"No usage tracker for org: {org_id}")
    return org.usage_tracker


# ── Shared implementation ────────────────────────────────────────────


def _list_usage(
    org_id: str,
    date_from: str | None,
    date_to: str | None,
    agent_id: str | None,
    model: str | None,
    limit: int,
    offset: int,
):
    tracker = _get_usage_tracker(org_id)
    return tracker.query(
        date_from=date_from,
        date_to=date_to,
        agent_id=agent_id,
        model=model,
        limit=limit,
        offset=offset,
    )


def _get_summary(org_id: str, date_from: str | None, date_to: str | None):
    tracker = _get_usage_tracker(org_id)
    return tracker.summary(date_from=date_from, date_to=date_to)


# ── Org-scoped routes ────────────────────────────────────────────────


@org_router.get("")
async def list_usage_org(
    org_id: str,
    date_from: str | None = None,
    date_to: str | None = None,
    agent_id: str | None = None,
    model: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    return _list_usage(org_id, date_from, date_to, agent_id, model, limit, offset)


@org_router.get("/summary")
async def usage_summary_org(
    org_id: str,
    date_from: str | None = None,
    date_to: str | None = None,
):
    return _get_summary(org_id, date_from, date_to)


# ── Legacy routes ────────────────────────────────────────────────────


@router.get("")
async def list_usage_legacy(
    date_from: str | None = None,
    date_to: str | None = None,
    agent_id: str | None = None,
    model: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    return _list_usage(
        registry.default_org_id, date_from, date_to, agent_id, model, limit, offset,
    )


@router.get("/summary")
async def usage_summary_legacy(
    date_from: str | None = None,
    date_to: str | None = None,
):
    return _get_summary(registry.default_org_id, date_from, date_to)

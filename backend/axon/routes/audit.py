"""Audit log routes — view append-only tool execution history."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

import axon.registry as registry

router = APIRouter()
org_router = APIRouter()


def _get_audit_logger(org_id: str):
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Organization not found: {org_id}")
    if not org.audit_logger:
        raise HTTPException(404, f"No audit logger for org: {org_id}")
    return org.audit_logger


def _list_audit(
    org_id: str,
    date_from: str | None,
    date_to: str | None,
    agent_id: str | None,
    action: str | None,
    tool: str | None,
    limit: int,
    offset: int,
):
    logger = _get_audit_logger(org_id)
    entries = logger.list_entries(
        date_from=date_from,
        date_to=date_to,
        agent_id=agent_id,
        action=action,
        tool=tool,
        limit=limit,
        offset=offset,
    )
    total = logger.count_entries()
    return {"entries": entries, "total": total, "limit": limit, "offset": offset}


# ── Org-scoped routes ─────────────────────────────────────────────────


@org_router.get("")
async def list_audit_org(
    org_id: str,
    date_from: str | None = None,
    date_to: str | None = None,
    agent_id: str | None = None,
    action: str | None = None,
    tool: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    return _list_audit(org_id, date_from, date_to, agent_id, action, tool, limit, offset)


# ── Legacy routes ─────────────────────────────────────────────────────


@router.get("")
async def list_audit_legacy(
    date_from: str | None = None,
    date_to: str | None = None,
    agent_id: str | None = None,
    action: str | None = None,
    tool: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    return _list_audit(
        registry.default_org_id, date_from, date_to, agent_id, action, tool, limit, offset
    )

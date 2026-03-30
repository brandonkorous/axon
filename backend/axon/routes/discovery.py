"""Capability discovery routes — human-facing management of requests and gaps."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import axon.registry as registry
from axon.discovery.models import RequestStatus
from axon.discovery.searcher import search_capabilities
from axon.discovery.store import list_requests, resolve_request

logger = logging.getLogger(__name__)

org_router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_org_or_404(org_id: str):
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Org not found: {org_id}")
    return org


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

@org_router.get("/search")
async def search(org_id: str, q: str = "", category: str = "", type: str = ""):
    """Search available capabilities across all registries."""
    _get_org_or_404(org_id)

    if not q:
        raise HTTPException(400, "query parameter 'q' is required")

    matches = search_capabilities(query=q, category=category, cap_type=type)
    return {
        "query": q,
        "count": len(matches),
        "results": [m.model_dump() for m in matches],
    }


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

@org_router.get("/requests")
async def get_requests(
    org_id: str,
    status: str = "",
    agent_id: str = "",
    gaps_only: bool = False,
):
    """List capability requests with optional filters."""
    _get_org_or_404(org_id)

    status_filter = RequestStatus(status) if status else None
    requests = list_requests(
        org_id,
        status=status_filter,
        agent_id=agent_id,
        gaps_only=gaps_only,
    )
    return {
        "count": len(requests),
        "requests": [r.model_dump() for r in requests],
    }


class ResolveRequest(BaseModel):
    status: str  # approved, rejected, building, available
    resolved_by: str = "human"
    note: str = ""


@org_router.post("/requests/{request_id}/resolve")
async def resolve(org_id: str, request_id: str, body: ResolveRequest):
    """Resolve a capability request (approve, reject, etc.)."""
    org = _get_org_or_404(org_id)

    try:
        new_status = RequestStatus(body.status)
    except ValueError:
        raise HTTPException(400, f"Invalid status: {body.status}")

    shared_vault = getattr(org, "shared_vault", None)
    updated = resolve_request(
        org_id,
        request_id,
        status=new_status,
        resolved_by=body.resolved_by,
        note=body.note,
        shared_vault=shared_vault,
    )

    if not updated:
        raise HTTPException(404, f"Request not found: {request_id}")

    # If approved and it's an existing capability, auto-enable for the agent
    if new_status == RequestStatus.APPROVED and not updated.is_gap and updated.capability_name:
        agent = org.agent_registry.get(updated.agent_id)
        if agent and hasattr(agent, "config"):
            _enable_for_agent(agent, updated.capability_type, updated.capability_name)
            resolve_request(
                org_id, request_id,
                status=RequestStatus.ENABLED,
                resolved_by=body.resolved_by,
                note=f"Auto-enabled after approval. {body.note}".strip(),
                shared_vault=shared_vault,
            )

    return {"request": updated.model_dump()}


def _enable_for_agent(agent, cap_type, name: str) -> None:
    """Enable a capability on an agent's config."""
    config = agent.config
    if cap_type == "plugin" and name not in config.plugins.enabled:
        config.plugins.enabled.append(name)
    elif cap_type == "skill" and name not in config.skills.enabled:
        config.skills.enabled.append(name)
    elif cap_type == "integration" and name not in config.integrations.enabled:
        config.integrations.enabled.append(name)

    # Rebuild tools if the agent supports it
    if hasattr(agent, "tools") and hasattr(agent, "_build_tool_list"):
        agent.tools = agent._build_tool_list()

"""Agent lifecycle routes — pause, resume, disable, terminate, delete, strategy override."""

from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from axon.config import settings
from axon.logging import get_logger
import axon.registry as registry

logger = get_logger(__name__)

router = APIRouter()
org_router = APIRouter()


class StrategyOverride(BaseModel):
    prompt: str


class RateLimitUpdate(BaseModel):
    max_per_minute: int


def _get_agent(org_id: str, agent_id: str):
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Organization not found: {org_id}")
    agent = org.agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(404, f"Agent not found: {agent_id}")
    return agent


# ── Shared handlers ───────────────────────────────────────────────────


def _get_state(org_id: str, agent_id: str):
    agent = _get_agent(org_id, agent_id)
    return agent.lifecycle.to_dict()


def _pause(org_id: str, agent_id: str):
    agent = _get_agent(org_id, agent_id)
    msg = agent.lifecycle.pause()
    return {"message": msg, "state": agent.lifecycle.to_dict()}


def _resume(org_id: str, agent_id: str):
    agent = _get_agent(org_id, agent_id)
    msg, queued = agent.lifecycle.resume()
    return {"message": msg, "queued_messages": len(queued), "state": agent.lifecycle.to_dict()}


def _disable(org_id: str, agent_id: str):
    agent = _get_agent(org_id, agent_id)
    msg = agent.lifecycle.disable()
    return {"message": msg, "state": agent.lifecycle.to_dict()}


def _enable(org_id: str, agent_id: str):
    agent = _get_agent(org_id, agent_id)
    msg = agent.lifecycle.enable()
    return {"message": msg, "state": agent.lifecycle.to_dict()}


def _terminate(org_id: str, agent_id: str):
    agent = _get_agent(org_id, agent_id)
    msg = agent.lifecycle.terminate()

    # Refresh rosters so terminated agent is still visible but won't receive new work
    org = registry.get_org(org_id)
    if org:
        from axon.routes.recruitment import _refresh_orchestrator_roster, _rebuild_peer_rosters
        _refresh_orchestrator_roster(org)
        _rebuild_peer_rosters(org)

    return {"message": msg, "state": agent.lifecycle.to_dict()}


def _delete_agent(org_id: str, agent_id: str):
    """Permanently delete an agent — removes from registry, deletes vault and state."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Organization not found: {org_id}")
    agent = org.agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(404, f"Agent not found: {agent_id}")

    # Protect core agents (orchestrator, huddle) from deletion
    if hasattr(agent, "config") and agent.config.type.value in ("orchestrator", "huddle"):
        raise HTTPException(400, f"Cannot delete {agent.config.type.value} agents")

    # Get vault path before removing from registry
    vault_path = Path(agent.config.vault.path) if hasattr(agent, "config") else None

    # Unregister from scheduler before removing from registry
    from axon.scheduler import scheduler
    scheduler.unregister_agent(org_id, agent_id)

    # Remove from registry
    del org.agent_registry[agent_id]

    # Delete lifecycle state file
    orgs_dir = settings.axon_orgs_dir
    if orgs_dir:
        state_file = Path(orgs_dir) / org_id / "data" / "agent-state" / f"{agent_id}.json"
        if state_file.exists():
            state_file.unlink()

    # Delete vault directory
    if vault_path and vault_path.exists():
        shutil.rmtree(vault_path)
        logger.info("Deleted vault for agent '%s': %s", agent_id, vault_path)

    # Refresh rosters so deleted agent disappears from everyone's view
    from axon.routes.recruitment import _refresh_orchestrator_roster, _rebuild_peer_rosters
    _refresh_orchestrator_roster(org)
    _rebuild_peer_rosters(org)

    logger.info("Agent '%s' permanently deleted from org '%s'", agent_id, org_id)
    return {"message": f"Agent '{agent_id}' permanently deleted.", "agent_id": agent_id}


def _set_strategy(org_id: str, agent_id: str, prompt: str):
    agent = _get_agent(org_id, agent_id)
    msg = agent.lifecycle.set_strategy_override(prompt)
    return {"message": msg, "state": agent.lifecycle.to_dict()}


def _clear_strategy(org_id: str, agent_id: str):
    agent = _get_agent(org_id, agent_id)
    msg = agent.lifecycle.clear_strategy_override()
    return {"message": msg, "state": agent.lifecycle.to_dict()}


def _set_rate_limit(org_id: str, agent_id: str, max_per_minute: int):
    agent = _get_agent(org_id, agent_id)
    msg = agent.lifecycle.set_rate_limit(max_per_minute)
    return {"message": msg, "state": agent.lifecycle.to_dict()}


# ── Org-scoped routes ─────────────────────────────────────────────────


@org_router.get("/{agent_id}/state")
async def get_state_org(org_id: str, agent_id: str):
    return _get_state(org_id, agent_id)


@org_router.post("/{agent_id}/pause")
async def pause_org(org_id: str, agent_id: str):
    return _pause(org_id, agent_id)


@org_router.post("/{agent_id}/resume")
async def resume_org(org_id: str, agent_id: str):
    return _resume(org_id, agent_id)


@org_router.post("/{agent_id}/disable")
async def disable_org(org_id: str, agent_id: str):
    return _disable(org_id, agent_id)


@org_router.post("/{agent_id}/enable")
async def enable_org(org_id: str, agent_id: str):
    return _enable(org_id, agent_id)


@org_router.post("/{agent_id}/terminate")
async def terminate_org(org_id: str, agent_id: str):
    return _terminate(org_id, agent_id)


@org_router.delete("/{agent_id}")
async def delete_agent_org(org_id: str, agent_id: str):
    return _delete_agent(org_id, agent_id)


@org_router.post("/{agent_id}/strategy-override")
async def set_strategy_org(org_id: str, agent_id: str, data: StrategyOverride):
    return _set_strategy(org_id, agent_id, data.prompt)


@org_router.delete("/{agent_id}/strategy-override")
async def clear_strategy_org(org_id: str, agent_id: str):
    return _clear_strategy(org_id, agent_id)


@org_router.post("/{agent_id}/rate-limit")
async def set_rate_limit_org(org_id: str, agent_id: str, data: RateLimitUpdate):
    return _set_rate_limit(org_id, agent_id, data.max_per_minute)


# ── Legacy routes ─────────────────────────────────────────────────────


@router.get("/{agent_id}/state")
async def get_state_legacy(agent_id: str):
    return _get_state(registry.default_org_id, agent_id)


@router.post("/{agent_id}/pause")
async def pause_legacy(agent_id: str):
    return _pause(registry.default_org_id, agent_id)


@router.post("/{agent_id}/resume")
async def resume_legacy(agent_id: str):
    return _resume(registry.default_org_id, agent_id)


@router.post("/{agent_id}/disable")
async def disable_legacy(agent_id: str):
    return _disable(registry.default_org_id, agent_id)


@router.post("/{agent_id}/enable")
async def enable_legacy(agent_id: str):
    return _enable(registry.default_org_id, agent_id)


@router.post("/{agent_id}/terminate")
async def terminate_legacy(agent_id: str):
    return _terminate(registry.default_org_id, agent_id)


@router.delete("/{agent_id}")
async def delete_agent_legacy(agent_id: str):
    return _delete_agent(registry.default_org_id, agent_id)


@router.post("/{agent_id}/strategy-override")
async def set_strategy_legacy(agent_id: str, data: StrategyOverride):
    return _set_strategy(registry.default_org_id, agent_id, data.prompt)


@router.delete("/{agent_id}/strategy-override")
async def clear_strategy_legacy(agent_id: str):
    return _clear_strategy(registry.default_org_id, agent_id)


@router.post("/{agent_id}/rate-limit")
async def set_rate_limit_legacy(agent_id: str, data: RateLimitUpdate):
    return _set_rate_limit(registry.default_org_id, agent_id, data.max_per_minute)

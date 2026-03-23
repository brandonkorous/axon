"""Agent lifecycle routes — pause, resume, disable, terminate, strategy override."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import axon.registry as registry

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
    return {"message": msg, "state": agent.lifecycle.to_dict()}


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


@router.post("/{agent_id}/strategy-override")
async def set_strategy_legacy(agent_id: str, data: StrategyOverride):
    return _set_strategy(registry.default_org_id, agent_id, data.prompt)


@router.delete("/{agent_id}/strategy-override")
async def clear_strategy_legacy(agent_id: str):
    return _clear_strategy(registry.default_org_id, agent_id)


@router.post("/{agent_id}/rate-limit")
async def set_rate_limit_legacy(agent_id: str, data: RateLimitUpdate):
    return _set_rate_limit(registry.default_org_id, agent_id, data.max_per_minute)

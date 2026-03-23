"""Agent management routes — list, status, CRUD."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

import axon.registry as registry

router = APIRouter()
org_router = APIRouter()


def _list_agents_for_registry(agent_reg: dict) -> list[dict]:
    """Build agent list from a registry dict."""
    agents = []
    for agent_id, agent in agent_reg.items():
        agents.append({
            "id": agent.id,
            "name": agent.name,
            "title": agent.config.title,
            "tagline": agent.config.tagline,
            "ui": {
                "color": agent.config.ui.color,
                "avatar": agent.config.ui.avatar,
                "sparkle_color": agent.config.ui.sparkle_color,
            },
            "type": agent.config.type.value if hasattr(agent.config, "type") else "advisor",
            "model": agent.config.model.reasoning,
            "status": agent.lifecycle.status.value if hasattr(agent, "lifecycle") else "idle",
            "lifecycle": agent.lifecycle.to_dict() if hasattr(agent, "lifecycle") else None,
        })
    return agents


def _get_agent_detail(agent) -> dict:
    """Build agent detail dict."""
    return {
        "id": agent.id,
        "name": agent.name,
        "title": agent.config.title,
        "tagline": agent.config.tagline,
        "ui": {
            "color": agent.config.ui.color,
            "avatar": agent.config.ui.avatar,
            "sparkle_color": agent.config.ui.sparkle_color,
        },
        "model": agent.config.model.reasoning,
        "vault": {
            "path": agent.config.vault.path,
            "root_file": agent.config.vault.root_file,
        },
        "delegation": {
            "can_delegate_to": agent.config.delegation.can_delegate_to,
            "accepts_from": agent.config.delegation.accepts_from,
        },
        "status": agent.lifecycle.status.value if hasattr(agent, "lifecycle") else "idle",
        "lifecycle": agent.lifecycle.to_dict() if hasattr(agent, "lifecycle") else None,
    }


# ── Legacy routes (default org) ─────────────────────────────────────


@router.get("")
async def list_agents():
    """List all available agents with their status."""
    return {"agents": _list_agents_for_registry(registry.agent_registry)}


@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    """Get details for a specific agent."""
    agent = registry.agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return _get_agent_detail(agent)


# ── Org-scoped routes ───────────────────────────────────────────────


@org_router.get("")
async def list_org_agents(org_id: str):
    """List all agents in an organization."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization not found: {org_id}")
    return {"agents": _list_agents_for_registry(org.agent_registry)}


@org_router.get("/{agent_id}")
async def get_org_agent(org_id: str, agent_id: str):
    """Get details for a specific agent in an organization."""
    agent = registry.get_agent(org_id, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id} in org {org_id}")
    return _get_agent_detail(agent)

"""Agent management routes — list, status, CRUD."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from axon.main import agent_registry

router = APIRouter()


@router.get("")
async def list_agents():
    """List all available agents with their status."""
    agents = []
    for agent_id, agent in agent_registry.items():
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
            "model": agent.config.model.reasoning,
            "status": "idle",  # TODO: track active conversations
        })
    return {"agents": agents}


@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    """Get details for a specific agent."""
    agent = agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

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
        "status": "idle",
    }

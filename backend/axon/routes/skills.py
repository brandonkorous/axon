"""Skill management routes — list, enable, disable, detail."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import axon.registry as registry
from axon.skills.registry import SKILL_REGISTRY, list_skills

logger = logging.getLogger(__name__)

org_router = APIRouter()


@org_router.get("")
async def list_all_skills(org_id: str):
    """List all registered skills with metadata."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Org not found: {org_id}")
    return {"skills": list_skills()}


@org_router.get("/{skill_name}")
async def get_skill_detail(org_id: str, skill_name: str):
    """Get full details for a specific skill."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Org not found: {org_id}")

    cls = SKILL_REGISTRY.get(skill_name)
    if not cls:
        raise HTTPException(404, f"Skill not found: {skill_name}")

    instance = cls()
    m = instance.manifest
    tools = instance.get_tools()

    # Find which agents have this skill enabled
    agents_using: list[str] = []
    for aid, agent in org.agent_registry.items():
        if hasattr(agent, "config") and hasattr(agent.config, "skills"):
            enabled = agent.config.skills.enabled if agent.config.skills else []
            if skill_name in enabled:
                agents_using.append(aid)

    return {
        "name": m.name,
        "description": m.description,
        "version": m.version,
        "author": m.author,
        "category": m.category,
        "icon": m.icon,
        "auto_load": m.auto_load,
        "triggers": m.triggers,
        "tools": [
            {"name": t["function"]["name"], "description": t["function"].get("description", "")}
            for t in tools
        ],
        "required_credentials": m.required_credentials,
        "python_deps": m.python_deps,
        "agents_using": agents_using,
    }


class SkillToggleRequest(BaseModel):
    agent_id: str


@org_router.post("/{skill_name}/enable")
async def enable_skill(org_id: str, skill_name: str, body: SkillToggleRequest):
    """Enable a skill for an agent."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Org not found: {org_id}")
    if skill_name not in SKILL_REGISTRY:
        raise HTTPException(404, f"Skill not found: {skill_name}")

    agent = org.agent_registry.get(body.agent_id)
    if not agent or not hasattr(agent, "config"):
        raise HTTPException(404, f"Agent not found: {body.agent_id}")

    config = agent.config
    if not hasattr(config, "skills") or config.skills is None:
        from axon.skills.config import SkillsConfig
        config.skills = SkillsConfig()

    if skill_name not in config.skills.enabled:
        config.skills.enabled.append(skill_name)

    return {"status": "enabled", "skill": skill_name, "agent": body.agent_id}


@org_router.post("/{skill_name}/disable")
async def disable_skill(org_id: str, skill_name: str, body: SkillToggleRequest):
    """Disable a skill for an agent."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Org not found: {org_id}")

    agent = org.agent_registry.get(body.agent_id)
    if not agent or not hasattr(agent, "config"):
        raise HTTPException(404, f"Agent not found: {body.agent_id}")

    config = agent.config
    if hasattr(config, "skills") and config.skills:
        config.skills.enabled = [s for s in config.skills.enabled if s != skill_name]

    return {"status": "disabled", "skill": skill_name, "agent": body.agent_id}

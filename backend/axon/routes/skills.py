"""Cognitive skill management routes — list, detail, enable, disable, create, update, delete."""

from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from axon.config import settings
from axon.logging import get_logger
import axon.registry as registry
from axon.skills.registry import (
    SKILL_REGISTRY,
    SKILL_METHODOLOGY,
    SKILL_SOURCE,
    list_skills,
)

logger = get_logger(__name__)

org_router = APIRouter()

SNAKE_CASE_RE = re.compile(r"^[a-z][a-z0-9_]*$")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_org_or_404(org_id: str):
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Org not found: {org_id}")
    return org


def _get_skill_dir(org_id: str, skill_name: str) -> Path:
    return Path(settings.axon_orgs_dir) / org_id / "skills" / skill_name


def _agents_using_skill(org, skill_name: str) -> list[str]:
    """Return agent IDs that have *skill_name* enabled."""
    result: list[str] = []
    for aid, agent in org.agent_registry.items():
        if hasattr(agent, "config") and hasattr(agent.config, "skills"):
            enabled = agent.config.skills.enabled if agent.config.skills else []
            if skill_name in enabled:
                result.append(aid)
    return result


def _disable_skill_for_all(org, skill_name: str) -> list[str]:
    """Remove *skill_name* from every agent that has it enabled."""
    affected: list[str] = []
    for aid, agent in org.agent_registry.items():
        if hasattr(agent, "config") and hasattr(agent.config, "skills") and agent.config.skills:
            if skill_name in agent.config.skills.enabled:
                agent.config.skills.enabled = [
                    s for s in agent.config.skills.enabled if s != skill_name
                ]
                affected.append(aid)
    return affected


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class SkillToggleRequest(BaseModel):
    agent_id: str


class SkillCreateRequest(BaseModel):
    name: str
    description: str = ""
    version: str = "1.0.0"
    author: str = "axon"
    category: str = "general"
    icon: str = ""
    triggers: list[str] = []
    auto_inject: bool = False
    methodology: str = ""  # the markdown content


class SkillUpdateRequest(BaseModel):
    description: str | None = None
    version: str | None = None
    author: str | None = None
    category: str | None = None
    icon: str | None = None
    triggers: list[str] | None = None
    auto_inject: bool | None = None
    methodology: str | None = None


# ---------------------------------------------------------------------------
# Read endpoints
# ---------------------------------------------------------------------------

@org_router.get("")
async def list_all_skills(org_id: str):
    """List all registered cognitive skills with metadata."""
    _get_org_or_404(org_id)
    return {"skills": list_skills()}


@org_router.get("/{skill_name}")
async def get_skill_detail(org_id: str, skill_name: str):
    """Get full details for a specific cognitive skill."""
    org = _get_org_or_404(org_id)

    defn = SKILL_REGISTRY.get(skill_name)
    if not defn:
        raise HTTPException(404, f"Skill not found: {skill_name}")

    return {
        "name": defn.name,
        "description": defn.description,
        "version": defn.version,
        "author": defn.author,
        "category": defn.category,
        "icon": defn.icon,
        "triggers": defn.triggers,
        "auto_inject": defn.auto_inject,
        "methodology": SKILL_METHODOLOGY.get(skill_name, ""),
        "agents_using": _agents_using_skill(org, skill_name),
        "is_builtin": SKILL_SOURCE.get(skill_name, "builtin") == "builtin",
        "source": SKILL_SOURCE.get(skill_name, "builtin"),
    }


# Import CRUD routes so they register on org_router
import axon.routes.skills_crud  # noqa: E402, F401

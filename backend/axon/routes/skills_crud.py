"""Cognitive skill CRUD routes — enable, disable, create, update, delete."""

from __future__ import annotations

import logging
import shutil

import yaml
from fastapi import HTTPException

from axon.config import settings
from axon.skills.loader import load_skill_from_directory
from axon.skills.registry import (
    SKILL_REGISTRY,
    SKILL_SOURCE,
    unregister_skill,
)
from axon.routes.skills import (
    SNAKE_CASE_RE,
    SkillCreateRequest,
    SkillToggleRequest,
    SkillUpdateRequest,
    _disable_skill_for_all,
    _get_org_or_404,
    _get_skill_dir,
    get_skill_detail,
    org_router,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enable / Disable
# ---------------------------------------------------------------------------

@org_router.post("/{skill_name}/enable")
async def enable_skill(org_id: str, skill_name: str, body: SkillToggleRequest):
    """Enable a cognitive skill for an agent."""
    org = _get_org_or_404(org_id)
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
    """Disable a cognitive skill for an agent."""
    org = _get_org_or_404(org_id)

    agent = org.agent_registry.get(body.agent_id)
    if not agent or not hasattr(agent, "config"):
        raise HTTPException(404, f"Agent not found: {body.agent_id}")

    config = agent.config
    if hasattr(config, "skills") and config.skills:
        config.skills.enabled = [s for s in config.skills.enabled if s != skill_name]

    return {"status": "disabled", "skill": skill_name, "agent": body.agent_id}


# ---------------------------------------------------------------------------
# Create / Update / Delete
# ---------------------------------------------------------------------------

@org_router.post("")
async def create_skill(org_id: str, body: SkillCreateRequest):
    """Create a new custom cognitive skill on disk and register it."""
    _get_org_or_404(org_id)

    if not SNAKE_CASE_RE.match(body.name):
        raise HTTPException(400, "Skill name must be snake_case (lowercase letters, digits, underscores)")
    if body.name in SKILL_REGISTRY:
        raise HTTPException(409, f"Skill already exists: {body.name}")

    skill_dir = _get_skill_dir(org_id, body.name)
    skill_dir.mkdir(parents=True, exist_ok=True)

    # Write skill.yaml
    manifest_data = body.model_dump(exclude={"methodology"})
    with open(skill_dir / "skill.yaml", "w", encoding="utf-8") as f:
        yaml.dump(manifest_data, f, default_flow_style=False, sort_keys=False)

    # Write methodology.md
    with open(skill_dir / "methodology.md", "w", encoding="utf-8") as f:
        f.write(body.methodology)

    # Load and register
    if not load_skill_from_directory(skill_dir, source="external"):
        shutil.rmtree(skill_dir, ignore_errors=True)
        raise HTTPException(500, "Failed to load skill after creation")

    logger.info("Created skill: %s in %s", body.name, skill_dir)
    return await get_skill_detail(org_id, body.name)


@org_router.put("/{skill_name}")
async def update_skill(org_id: str, skill_name: str, body: SkillUpdateRequest):
    """Update a custom cognitive skill's metadata and/or methodology."""
    _get_org_or_404(org_id)

    if skill_name not in SKILL_REGISTRY:
        raise HTTPException(404, f"Skill not found: {skill_name}")
    if SKILL_SOURCE.get(skill_name, "builtin") == "builtin":
        raise HTTPException(403, "Cannot edit built-in skills")

    skill_dir = _get_skill_dir(org_id, skill_name)
    manifest_path = skill_dir / "skill.yaml"
    if not manifest_path.exists():
        raise HTTPException(404, f"Skill manifest not found on disk: {skill_name}")

    # Read, merge, write skill.yaml
    with open(manifest_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    updates = body.model_dump(exclude_none=True, exclude={"methodology"})
    data.update(updates)

    with open(manifest_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    # Update methodology.md if provided
    if body.methodology is not None:
        with open(skill_dir / "methodology.md", "w", encoding="utf-8") as f:
            f.write(body.methodology)

    # Re-register: unregister old, reload from disk
    unregister_skill(skill_name)
    if not load_skill_from_directory(skill_dir, source="external"):
        raise HTTPException(500, "Failed to reload skill after update")

    logger.info("Updated skill: %s", skill_name)
    return await get_skill_detail(org_id, skill_name)


@org_router.delete("/{skill_name}")
async def delete_skill(org_id: str, skill_name: str):
    """Delete a custom cognitive skill from disk and registry."""
    org = _get_org_or_404(org_id)

    if skill_name not in SKILL_REGISTRY:
        raise HTTPException(404, f"Skill not found: {skill_name}")
    if SKILL_SOURCE.get(skill_name, "builtin") == "builtin":
        raise HTTPException(403, "Cannot delete built-in skills")

    # Disable from all agents first
    agents_affected = _disable_skill_for_all(org, skill_name)

    # Remove from registry
    unregister_skill(skill_name)

    # Delete from disk
    skill_dir = _get_skill_dir(org_id, skill_name)
    if skill_dir.exists():
        shutil.rmtree(skill_dir)

    logger.info("Deleted skill: %s (affected agents: %s)", skill_name, agents_affected)
    return {"deleted": skill_name, "agents_affected": agents_affected}

"""Skill registry — discover, register, and instantiate skills."""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import Any

from axon.skills.base import BaseSkill

logger = logging.getLogger(__name__)

# Global registry: skill_name → skill class
SKILL_REGISTRY: dict[str, type[BaseSkill]] = {}


def register_skill(name: str, cls: type[BaseSkill]) -> None:
    """Register a skill class by name."""
    SKILL_REGISTRY[name] = cls
    logger.debug("Registered skill: %s", name)


def get_skill(name: str) -> type[BaseSkill] | None:
    """Look up a registered skill by name."""
    return SKILL_REGISTRY.get(name)


def list_skills() -> list[dict[str, Any]]:
    """Return manifest info for all registered skills."""
    result = []
    for name, cls in sorted(SKILL_REGISTRY.items()):
        instance = cls()
        m = instance.manifest
        result.append({
            "name": m.name,
            "description": m.description,
            "version": m.version,
            "author": m.author,
            "category": m.category,
            "icon": m.icon,
            "auto_load": m.auto_load,
            "triggers": m.triggers,
            "tools": [t["function"]["name"] for t in instance.get_tools()],
            "required_credentials": m.required_credentials,
        })
    return result


def get_tools_for_skills(names: list[str]) -> list[dict[str, Any]]:
    """Collect tool schemas from all named skills."""
    tools: list[dict[str, Any]] = []
    for name in names:
        cls = SKILL_REGISTRY.get(name)
        if cls:
            instance = cls()
            tools.extend(instance.get_tools())
    return tools


def create_skill_executor(
    names: list[str],
    credentials_map: dict[str, dict[str, Any]] | None = None,
) -> "SkillToolExecutor | None":
    """Create an executor for the given skill names."""
    from axon.skills.executor import SkillToolExecutor

    if not names:
        return None

    skills: list[BaseSkill] = []
    for name in names:
        cls = SKILL_REGISTRY.get(name)
        if cls:
            instance = cls()
            instance.configure((credentials_map or {}).get(name))
            skills.append(instance)
        else:
            logger.warning("Skill not found: %s", name)

    return SkillToolExecutor(skills) if skills else None


def discover_skills() -> None:
    """Import all built-in skill modules to trigger registration.

    Also scans for external skill packages in the skills directory.
    """
    _discover_builtin()
    _discover_external()


def _discover_builtin() -> None:
    """Import built-in skill subpackages."""
    builtin_dir = Path(__file__).parent / "builtin"
    if not builtin_dir.exists():
        return

    for child in sorted(builtin_dir.iterdir()):
        if child.is_dir() and (child / "__init__.py").exists() and child.name != "__pycache__":
            try:
                importlib.import_module(f"axon.skills.builtin.{child.name}")
                logger.debug("Discovered built-in skill: %s", child.name)
            except Exception as e:
                logger.warning("Failed to load skill %s: %s", child.name, e)


def _discover_external() -> None:
    """Discover external skills from the skills directory.

    External skills live in orgs/{org}/skills/ directories and are
    discovered at runtime. Each must have a skill.yaml and __init__.py.
    """
    # External skill loading is deferred — requires org context
    pass

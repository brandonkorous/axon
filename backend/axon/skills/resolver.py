"""Skill resolver — determine which skills to activate for a given message."""

from __future__ import annotations

import logging
from typing import Any

from axon.skills.base import BaseSkill
from axon.skills.registry import SKILL_REGISTRY

logger = logging.getLogger(__name__)


def resolve_skills(
    message: str,
    enabled_skills: list[str],
    always_loaded: list[str] | None = None,
) -> list[str]:
    """Determine which skills should be active for this message.

    Returns a list of skill names that should have their tools
    available to the agent for this turn.

    Priority:
    1. Skills marked auto_load that are in enabled_skills
    2. Skills in always_loaded list
    3. Skills whose triggers match the message content
    """
    active: set[str] = set()

    # Always-on skills
    for name in (always_loaded or []):
        if name in SKILL_REGISTRY:
            active.add(name)

    for name in enabled_skills:
        cls = SKILL_REGISTRY.get(name)
        if not cls:
            continue

        instance = cls()

        # Auto-load skills are always active
        if instance.manifest.auto_load:
            active.add(name)
            continue

        # Check trigger keywords
        if instance.matches_trigger(message):
            active.add(name)
            logger.debug("Skill '%s' activated by trigger match", name)

    return sorted(active)


def get_skill_tools(
    skill_names: list[str],
    credentials_map: dict[str, dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, BaseSkill]]:
    """Collect tool schemas and handler map for a set of skills.

    Returns (tool_schemas, handler_map) where handler_map maps
    tool_name → skill_instance for routing.
    """
    tools: list[dict[str, Any]] = []
    handlers: dict[str, BaseSkill] = {}

    for name in skill_names:
        cls = SKILL_REGISTRY.get(name)
        if not cls:
            continue

        instance = cls()
        instance.configure((credentials_map or {}).get(name))

        for schema in instance.get_tools():
            tool_name = schema.get("function", {}).get("name", "")
            if tool_name:
                tools.append(schema)
                handlers[tool_name] = instance

    return tools, handlers

"""SkillToolExecutor — routes tool calls to the correct skill."""

from __future__ import annotations

import json
import logging
from typing import Any

from axon.skills.base import BaseSkill

logger = logging.getLogger(__name__)


class SkillToolExecutor:
    """Routes tool calls to their owning skill instance."""

    def __init__(self, skills: list[BaseSkill]) -> None:
        self._skills = skills
        self._handler_map: dict[str, BaseSkill] = {}
        self._tools: list[dict[str, Any]] = []

        for skill in skills:
            tool_schemas = skill.get_tools()
            self._tools.extend(tool_schemas)
            for schema in tool_schemas:
                name = schema.get("function", {}).get("name", "")
                if name:
                    self._handler_map[name] = skill

    @property
    def tools(self) -> list[dict[str, Any]]:
        """All tool schemas from all managed skills."""
        return list(self._tools)

    @property
    def tool_names(self) -> set[str]:
        """Set of all tool names handled by this executor."""
        return set(self._handler_map.keys())

    def can_handle(self, tool_name: str) -> bool:
        """Check if this executor handles a given tool name."""
        return tool_name in self._handler_map

    async def execute(self, tool_name: str, arguments: str) -> str:
        """Execute a tool call, routing to the correct skill."""
        skill = self._handler_map.get(tool_name)
        if not skill:
            return json.dumps({"error": f"No skill handles tool: {tool_name}"})

        try:
            return await skill.execute(tool_name, arguments)
        except Exception as e:
            logger.exception("Skill %s failed on tool %s", skill.name, tool_name)
            return json.dumps({"error": f"Skill error: {e}"})

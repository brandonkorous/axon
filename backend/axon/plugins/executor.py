"""PluginToolExecutor — routes tool calls to the correct plugin."""

from __future__ import annotations

import json
import logging
from typing import Any

from axon.plugins.base import BasePlugin

logger = logging.getLogger(__name__)


class PluginToolExecutor:
    """Routes tool calls to their owning plugin instance."""

    def __init__(self, plugins: list[BasePlugin]) -> None:
        self._plugins = plugins
        self._handler_map: dict[str, BasePlugin] = {}
        self._tools: list[dict[str, Any]] = []

        for plugin in plugins:
            tool_schemas = plugin.get_tools()
            self._tools.extend(tool_schemas)
            for schema in tool_schemas:
                name = schema.get("function", {}).get("name", "")
                if name:
                    self._handler_map[name] = plugin

    @property
    def tools(self) -> list[dict[str, Any]]:
        """All tool schemas from all managed plugins."""
        return list(self._tools)

    @property
    def tool_names(self) -> set[str]:
        """Set of all tool names handled by this executor."""
        return set(self._handler_map.keys())

    def can_handle(self, tool_name: str) -> bool:
        """Check if this executor handles a given tool name."""
        return tool_name in self._handler_map

    async def execute(self, tool_name: str, arguments: str) -> str:
        """Execute a tool call, routing to the correct plugin."""
        plugin = self._handler_map.get(tool_name)
        if not plugin:
            return json.dumps({"error": f"No plugin handles tool: {tool_name}"})

        try:
            return await plugin.execute(tool_name, arguments)
        except Exception as e:
            logger.exception("Plugin %s failed on tool %s", plugin.name, tool_name)
            return json.dumps({"error": f"Plugin error: {e}"})

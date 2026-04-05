"""IntegrationToolExecutor — routes tool calls to integration instances."""

from __future__ import annotations

from typing import Any

from axon.integrations.base import BaseIntegration
from axon.logging import get_logger

logger = get_logger(__name__)


class IntegrationToolExecutor:
    """Routes tool calls to the correct integration instance.

    Follows the same pattern as CommsToolExecutor and WebToolExecutor:
    collect tools from all integrations, dispatch by tool name.
    """

    def __init__(self, integrations: list[BaseIntegration]):
        self._handler_map: dict[str, BaseIntegration] = {}
        self._integrations = integrations
        for integration in integrations:
            for tool in integration.get_tools():
                tool_name = tool["function"]["name"]
                self._handler_map[tool_name] = integration

    def get_tools(self) -> list[dict[str, Any]]:
        """Collect tool schemas from all managed integrations."""
        tools: list[dict[str, Any]] = []
        seen: set[int] = set()
        for integration in self._integrations:
            if id(integration) not in seen:
                seen.add(id(integration))
                tools.extend(integration.get_tools())
        return tools

    async def execute(self, tool_name: str, arguments: str) -> str:
        """Execute a tool call by routing to the appropriate integration."""
        integration = self._handler_map.get(tool_name)
        if not integration:
            return f"Error: No integration handles tool: {tool_name}"

        try:
            return await integration.execute(tool_name, arguments)
        except Exception as e:
            logger.exception("Integration tool error: %s", tool_name)
            return f"Error executing {tool_name}: {e}"

"""Base class for all Axon integrations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseIntegration(ABC):
    """Abstract base for external service integrations.

    Each integration provides:
    - A set of LLM tool schemas (OpenAI function calling format)
    - An executor that handles tool calls for those tools

    Integrations are registered in the integration registry and
    enabled per-agent via IntegrationConfig.enabled list.
    """

    name: str = ""

    @abstractmethod
    def get_tools(self) -> list[dict[str, Any]]:
        """Return tool schemas for this integration."""
        ...

    @abstractmethod
    async def execute(self, tool_name: str, arguments: str) -> str:
        """Execute a tool call for this integration."""
        ...

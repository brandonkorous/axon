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
    description: str = ""
    required_scopes: list[str] = []
    tool_prefix: str = ""

    def configure(self, credentials: dict[str, Any] | None = None) -> None:
        """Inject credentials after instantiation. Override if needed."""
        self._credentials = credentials or {}

    @abstractmethod
    def get_tools(self) -> list[dict[str, Any]]:
        """Return tool schemas for this integration."""
        ...

    @abstractmethod
    async def execute(self, tool_name: str, arguments: str) -> str:
        """Execute a tool call for this integration."""
        ...

    async def on_agent_start(self, agent_id: str) -> None:
        """Called when an agent with this integration starts up."""

    async def on_agent_message(self, agent_id: str, message: str) -> str | None:
        """Called before processing — can inject context. Return None to skip."""
        return None

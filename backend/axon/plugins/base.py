"""BasePlugin — abstract base class for all Axon plugins.

Extends the integration pattern with manifest-based metadata,
trigger-based activation, and lifecycle hooks for progressive loading.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from axon.plugins.manifest import PluginManifest


class BasePlugin(ABC):
    """Abstract base for all Axon plugins.

    A plugin provides:
    - A manifest describing its metadata and loading behavior
    - A set of LLM tool schemas (OpenAI function calling format)
    - An executor that handles tool calls
    - Optional lifecycle hooks for agent integration
    """

    manifest: PluginManifest

    def __init__(self) -> None:
        if not hasattr(self, "manifest"):
            raise NotImplementedError("Plugins must define a `manifest` class attribute")
        self._credentials: dict[str, Any] = {}
        self._loaded = False

    @property
    def name(self) -> str:
        return self.manifest.name

    @property
    def description(self) -> str:
        return self.manifest.description

    def configure(self, credentials: dict[str, Any] | None = None) -> None:
        """Inject credentials after instantiation."""
        self._credentials = credentials or {}

    @abstractmethod
    def get_tools(self) -> list[dict[str, Any]]:
        """Return tool schemas for this plugin."""
        ...

    @abstractmethod
    async def execute(self, tool_name: str, arguments: str) -> str:
        """Execute a tool call for this plugin."""
        ...

    async def on_load(self) -> None:
        """Called when the plugin is loaded for an agent. Override for setup."""
        self._loaded = True

    async def on_unload(self) -> None:
        """Called when the plugin is unloaded. Override for cleanup."""
        self._loaded = False

    async def on_agent_start(self, agent_id: str) -> None:
        """Called when an agent with this plugin starts."""

    async def on_agent_message(self, agent_id: str, message: str) -> str | None:
        """Called before processing — can inject context. Return None to skip."""
        return None

    def matches_trigger(self, text: str) -> bool:
        """Check if a message matches this plugin's trigger keywords."""
        if not self.manifest.triggers:
            return False
        lower = text.lower()
        return any(trigger.lower() in lower for trigger in self.manifest.triggers)

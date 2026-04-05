"""Plugin resolver — determine which plugins to activate for a given message."""

from __future__ import annotations

from typing import Any

from axon.logging import get_logger
from axon.plugins.base import BasePlugin
from axon.plugins.registry import PLUGIN_REGISTRY

logger = get_logger(__name__)


def resolve_plugins(
    message: str,
    enabled_plugins: list[str],
    always_loaded: list[str] | None = None,
) -> list[str]:
    """Determine which plugins should be active for this message.

    Returns a list of plugin names that should have their tools
    available to the agent for this turn.

    Priority:
    1. Plugins marked auto_load that are in enabled_plugins
    2. Plugins in always_loaded list
    3. Plugins whose triggers match the message content
    """
    active: set[str] = set()

    # Always-on plugins
    for name in (always_loaded or []):
        if name in PLUGIN_REGISTRY:
            active.add(name)

    for name in enabled_plugins:
        cls = PLUGIN_REGISTRY.get(name)
        if not cls:
            continue

        instance = cls()

        # Auto-load plugins are always active
        if instance.manifest.auto_load:
            active.add(name)
            continue

        # Check trigger keywords
        if instance.matches_trigger(message):
            active.add(name)
            logger.debug("Plugin '%s' activated by trigger match", name)

    return sorted(active)


def get_plugin_tools(
    plugin_names: list[str],
    credentials_map: dict[str, dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, BasePlugin]]:
    """Collect tool schemas and handler map for a set of plugins.

    Returns (tool_schemas, handler_map) where handler_map maps
    tool_name → plugin_instance for routing.
    """
    tools: list[dict[str, Any]] = []
    handlers: dict[str, BasePlugin] = {}

    for name in plugin_names:
        cls = PLUGIN_REGISTRY.get(name)
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

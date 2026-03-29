"""Plugin registry — discover, register, and instantiate plugins."""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import Any

from axon.plugins.base import BasePlugin

logger = logging.getLogger(__name__)

# Global registry: plugin_name → plugin class
PLUGIN_REGISTRY: dict[str, type[BasePlugin]] = {}

# Track whether each plugin is built-in, external, or an integration
PLUGIN_SOURCE: dict[str, str] = {}


def register_plugin(name: str, cls: type[BasePlugin], *, source: str = "builtin") -> None:
    """Register a plugin class by name."""
    PLUGIN_REGISTRY[name] = cls
    PLUGIN_SOURCE[name] = source
    logger.debug("Registered plugin: %s (source=%s)", name, source)


def unregister_plugin(name: str) -> None:
    """Remove a plugin from the registry."""
    PLUGIN_REGISTRY.pop(name, None)
    PLUGIN_SOURCE.pop(name, None)
    logger.debug("Unregistered plugin: %s", name)


def get_plugin(name: str) -> type[BasePlugin] | None:
    """Look up a registered plugin by name."""
    return PLUGIN_REGISTRY.get(name)


def list_plugins() -> list[dict[str, Any]]:
    """Return manifest info for all registered plugins."""
    result = []
    for name, cls in sorted(PLUGIN_REGISTRY.items()):
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
            "sandbox_type": m.sandbox_type,
            "is_builtin": PLUGIN_SOURCE.get(name, "builtin") != "external",
            "source": PLUGIN_SOURCE.get(name, "builtin"),
        })
    return result


def get_tools_for_plugins(names: list[str]) -> list[dict[str, Any]]:
    """Collect tool schemas from all named plugins."""
    tools: list[dict[str, Any]] = []
    for name in names:
        cls = PLUGIN_REGISTRY.get(name)
        if cls:
            instance = cls()
            tools.extend(instance.get_tools())
    return tools


def create_plugin_executor(
    names: list[str],
    credentials_map: dict[str, dict[str, Any]] | None = None,
) -> "PluginToolExecutor | None":
    """Create an executor for the given plugin names."""
    from axon.plugins.executor import PluginToolExecutor

    if not names:
        return None

    plugins: list[BasePlugin] = []
    for name in names:
        cls = PLUGIN_REGISTRY.get(name)
        if cls:
            instance = cls()
            instance.configure((credentials_map or {}).get(name))
            plugins.append(instance)
        else:
            logger.warning("Plugin not found: %s", name)

    return PluginToolExecutor(plugins) if plugins else None


def discover_plugins() -> None:
    """Import all built-in plugin modules and integration adapters.

    Also scans for external plugin packages in the plugins directory.
    """
    _discover_builtin()
    _discover_integrations()
    _discover_external()


def _discover_builtin() -> None:
    """Import built-in plugin subpackages."""
    builtin_dir = Path(__file__).parent / "builtin"
    if not builtin_dir.exists():
        return

    for child in sorted(builtin_dir.iterdir()):
        if child.is_dir() and (child / "__init__.py").exists() and child.name != "__pycache__":
            try:
                importlib.import_module(f"axon.plugins.builtin.{child.name}")
                logger.debug("Discovered built-in plugin: %s", child.name)
            except Exception as e:
                logger.warning("Failed to load plugin %s: %s", child.name, e)


def _discover_integrations() -> None:
    """Wrap existing BaseIntegration classes as plugins via adapter."""
    try:
        from axon.integrations.registry import INTEGRATION_REGISTRY
        from axon.plugins.compat import IntegrationPluginAdapter

        for name, cls in INTEGRATION_REGISTRY.items():
            if name not in PLUGIN_REGISTRY:
                # Create adapter subclass that captures the integration class
                def _make_adapter(integration_cls):
                    class Adapter(IntegrationPluginAdapter):
                        def __init__(self):
                            super().__init__(integration_cls)
                    return Adapter
                register_plugin(name, _make_adapter(cls), source="integration")
                logger.debug("Wrapped integration as plugin: %s", name)
    except ImportError:
        logger.debug("No integrations module found, skipping integration discovery")


def _discover_external() -> None:
    """Discover external plugins from the plugins directory.

    External plugins live in orgs/{org}/plugins/ directories and are
    discovered at runtime. Each must have a plugin.yaml and __init__.py.
    """
    # External plugin loading is deferred — requires org context
    pass

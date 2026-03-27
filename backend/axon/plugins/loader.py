"""Plugin loader — dynamic import and validation of plugin packages."""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import Any

import yaml

from axon.plugins.base import BasePlugin
from axon.plugins.manifest import PluginManifest
from axon.plugins.registry import register_plugin

logger = logging.getLogger(__name__)


def load_plugin_from_directory(plugin_dir: Path) -> type[BasePlugin] | None:
    """Load a plugin from a directory containing plugin.yaml and __init__.py.

    Returns the plugin class if successful, None otherwise.
    """
    manifest_path = plugin_dir / "plugin.yaml"
    init_path = plugin_dir / "__init__.py"

    if not manifest_path.exists():
        logger.warning("No plugin.yaml in %s", plugin_dir)
        return None
    if not init_path.exists():
        logger.warning("No __init__.py in %s", plugin_dir)
        return None

    # Load and validate manifest
    manifest = _load_manifest(manifest_path)
    if not manifest:
        return None

    # Import the module
    try:
        module_name = f"axon_plugin_{manifest.name}"
        spec = importlib.util.spec_from_file_location(module_name, init_path)
        if not spec or not spec.loader:
            logger.warning("Failed to create module spec for %s", plugin_dir)
            return None

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Look for the plugin class (must extend BasePlugin)
        plugin_cls = _find_plugin_class(module)
        if not plugin_cls:
            logger.warning("No BasePlugin subclass found in %s", plugin_dir)
            return None

        # Inject manifest if not already set
        if not hasattr(plugin_cls, "manifest") or plugin_cls.manifest is None:
            plugin_cls.manifest = manifest

        register_plugin(manifest.name, plugin_cls, source="external")
        logger.info("Loaded external plugin: %s v%s", manifest.name, manifest.version)
        return plugin_cls

    except Exception as e:
        logger.exception("Failed to load plugin from %s: %s", plugin_dir, e)
        return None


def load_org_plugins(orgs_dir: str, org_id: str) -> list[str]:
    """Discover and load plugins from an org's plugins directory.

    Returns list of loaded plugin names.
    """
    plugins_dir = Path(orgs_dir) / org_id / "plugins"
    if not plugins_dir.is_dir():
        return []

    loaded: list[str] = []
    for child in sorted(plugins_dir.iterdir()):
        if child.is_dir() and (child / "plugin.yaml").exists():
            cls = load_plugin_from_directory(child)
            if cls:
                loaded.append(cls().manifest.name)

    return loaded


def _load_manifest(path: Path) -> PluginManifest | None:
    """Parse and validate a plugin.yaml manifest file."""
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return PluginManifest(**data)
    except Exception as e:
        logger.warning("Invalid plugin manifest %s: %s", path, e)
        return None


def _find_plugin_class(module: Any) -> type[BasePlugin] | None:
    """Find the first BasePlugin subclass in a module."""
    for name in dir(module):
        obj = getattr(module, name)
        if (
            isinstance(obj, type)
            and issubclass(obj, BasePlugin)
            and obj is not BasePlugin
        ):
            return obj
    return None

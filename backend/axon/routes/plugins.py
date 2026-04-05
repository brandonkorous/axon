"""Plugin management routes — list, detail, enable, disable, create, update, delete."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from axon.config import settings
from axon.logging import get_logger
from axon.plugins.loader import load_plugin_from_directory
from axon.plugins.registry import (
    PLUGIN_REGISTRY,
    PLUGIN_SOURCE,
    list_plugins,
    unregister_plugin,
)
import axon.registry as registry

logger = get_logger(__name__)

org_router = APIRouter()

SNAKE_CASE_RE = re.compile(r"^[a-z][a-z0-9_]*$")

PLUGIN_SCAFFOLD = '''\
"""Auto-generated plugin scaffold."""

from __future__ import annotations

from typing import Any

from axon.plugins.base import BasePlugin


class Plugin(BasePlugin):
    """Stub plugin — edit get_tools() and execute() to add functionality."""

    def get_tools(self) -> list[dict[str, Any]]:
        return []

    async def execute(self, tool_name: str, arguments: str) -> str:
        return "Not implemented"
'''


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_org_or_404(org_id: str):
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Org not found: {org_id}")
    return org


def _get_plugin_dir(org_id: str, plugin_name: str) -> Path:
    return Path(settings.axon_orgs_dir) / org_id / "plugins" / plugin_name


def _persist_plugin_config(agent, plugin_name: str, *, enabled: bool) -> None:
    """Save plugin enabled state to agent.yaml."""
    yaml_path = Path(agent.config.vault.path) / "agent.yaml"
    if not yaml_path.exists():
        return
    try:
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        if "plugins" not in data:
            data["plugins"] = {}
        if "enabled" not in data["plugins"]:
            data["plugins"]["enabled"] = []

        current = data["plugins"]["enabled"]
        if enabled and plugin_name not in current:
            current.append(plugin_name)
        elif not enabled and plugin_name in current:
            data["plugins"]["enabled"] = [p for p in current if p != plugin_name]

        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    except Exception as e:
        logger.warning("Failed to persist plugin config for %s: %s", agent.id, e)


def _persist_plugin_config_data(agent, plugin_name: str, config_data: dict) -> None:
    """Save per-plugin config to agent.yaml."""
    yaml_path = Path(agent.config.vault.path) / "agent.yaml"
    if not yaml_path.exists():
        return
    try:
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        if "plugins" not in data:
            data["plugins"] = {}
        if "config" not in data["plugins"]:
            data["plugins"]["config"] = {}

        data["plugins"]["config"][plugin_name] = config_data

        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    except Exception as e:
        logger.warning("Failed to persist plugin config for %s/%s: %s", agent.id, plugin_name, e)


def _rebuild_agent_plugins(agent) -> None:
    """Rebuild plugin executor and tool list after enable/disable."""
    if hasattr(agent, '_build_plugin_executor'):
        agent._plugin_executor = agent._build_plugin_executor()
        if agent._plugin_executor:
            agent.tool_executor._plugin_executor = agent._plugin_executor
        else:
            agent.tool_executor._plugin_executor = None
        agent.tools = agent._build_tool_list()


def _agents_using_plugin(org, plugin_name: str) -> list[str]:
    """Return agent IDs that have *plugin_name* enabled (from org instances)."""
    return list({
        aid
        for inst in org.config.plugin_instances
        if inst.plugin == plugin_name
        for aid in inst.agents
    })


def _disable_plugin_for_all(org, plugin_name: str) -> list[str]:
    """Remove *plugin_name* from every agent that has it enabled."""
    affected: list[str] = []
    for aid, agent in org.agent_registry.items():
        if hasattr(agent, "config") and hasattr(agent.config, "plugins") and agent.config.plugins:
            if plugin_name in agent.config.plugins.enabled:
                agent.config.plugins.enabled = [
                    p for p in agent.config.plugins.enabled if p != plugin_name
                ]
                affected.append(aid)
    return affected


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class PluginToggleRequest(BaseModel):
    agent_id: str


class PluginCreateRequest(BaseModel):
    name: str
    description: str = ""
    version: str = "1.0.0"
    author: str = "axon"
    category: str = "general"
    icon: str = ""
    auto_load: bool = False
    triggers: list[str] = []
    tool_prefix: str = ""
    tools: list[str] = []
    python_deps: list[str] = []
    required_credentials: list[str] = []


class PluginUpdateRequest(BaseModel):
    description: str | None = None
    version: str | None = None
    author: str | None = None
    category: str | None = None
    icon: str | None = None
    auto_load: bool | None = None
    triggers: list[str] | None = None
    tool_prefix: str | None = None
    tools: list[str] | None = None
    python_deps: list[str] | None = None
    required_credentials: list[str] | None = None


class PluginConfigRequest(BaseModel):
    agent_id: str
    config: dict[str, Any]


# ---------------------------------------------------------------------------
# Read endpoints
# ---------------------------------------------------------------------------

@org_router.get("")
async def list_all_plugins(org_id: str):
    """List all registered plugins with metadata."""
    _get_org_or_404(org_id)
    return {"plugins": list_plugins()}


@org_router.get("/{plugin_name}")
async def get_plugin_detail(org_id: str, plugin_name: str):
    """Get full details for a specific plugin."""
    org = _get_org_or_404(org_id)

    cls = PLUGIN_REGISTRY.get(plugin_name)
    if not cls:
        raise HTTPException(404, f"Plugin not found: {plugin_name}")

    instance = cls()
    m = instance.manifest
    tools = instance.get_tools()

    # Collect instances for this plugin from org config
    instances = [
        i.model_dump() for i in org.config.plugin_instances
        if i.plugin == plugin_name
    ]
    # Derive agents_using from instances
    agents_using = list({
        aid for i in org.config.plugin_instances
        if i.plugin == plugin_name
        for aid in i.agents
    })

    return {
        "name": m.name,
        "description": m.description,
        "version": m.version,
        "author": m.author,
        "category": m.category,
        "icon": m.icon,
        "auto_load": m.auto_load,
        "triggers": m.triggers,
        "tools": [
            {"name": t["function"]["name"], "description": t["function"].get("description", "")}
            for t in tools
        ],
        "required_credentials": m.required_credentials,
        "python_deps": m.python_deps,
        "sandbox_type": m.sandbox_type,
        "agents_using": agents_using,
        "instances": instances,
        "is_builtin": PLUGIN_SOURCE.get(plugin_name, "builtin") != "external",
        "source": PLUGIN_SOURCE.get(plugin_name, "builtin"),
    }


# ---------------------------------------------------------------------------
# Enable / Disable
# ---------------------------------------------------------------------------

@org_router.post("/{plugin_name}/enable")
async def enable_plugin(org_id: str, plugin_name: str, body: PluginToggleRequest):
    """Enable a plugin for an agent."""
    org = _get_org_or_404(org_id)
    if plugin_name not in PLUGIN_REGISTRY:
        raise HTTPException(404, f"Plugin not found: {plugin_name}")

    agent = org.agent_registry.get(body.agent_id)
    if not agent or not hasattr(agent, "config"):
        raise HTTPException(404, f"Agent not found: {body.agent_id}")

    config = agent.config
    if not hasattr(config, "plugins") or config.plugins is None:
        from axon.plugins.config import PluginsConfig
        config.plugins = PluginsConfig()

    if plugin_name not in config.plugins.enabled:
        config.plugins.enabled.append(plugin_name)

    # Persist to agent.yaml
    _persist_plugin_config(agent, plugin_name, enabled=True)

    # Rebuild agent tools to include new plugin
    _rebuild_agent_plugins(agent)

    return {"status": "enabled", "plugin": plugin_name, "agent": body.agent_id}


@org_router.post("/{plugin_name}/disable")
async def disable_plugin(org_id: str, plugin_name: str, body: PluginToggleRequest):
    """Disable a plugin for an agent."""
    org = _get_org_or_404(org_id)

    agent = org.agent_registry.get(body.agent_id)
    if not agent or not hasattr(agent, "config"):
        raise HTTPException(404, f"Agent not found: {body.agent_id}")

    config = agent.config
    if hasattr(config, "plugins") and config.plugins:
        config.plugins.enabled = [p for p in config.plugins.enabled if p != plugin_name]

    # Persist to agent.yaml
    _persist_plugin_config(agent, plugin_name, enabled=False)

    # Rebuild agent tools to remove plugin
    _rebuild_agent_plugins(agent)

    return {"status": "disabled", "plugin": plugin_name, "agent": body.agent_id}


# ---------------------------------------------------------------------------
# Per-plugin configuration
# ---------------------------------------------------------------------------

@org_router.get("/{plugin_name}/config/{agent_id}")
async def get_plugin_config(org_id: str, plugin_name: str, agent_id: str):
    """Get plugin configuration for a specific agent."""
    org = _get_org_or_404(org_id)
    agent = org.agent_registry.get(agent_id)
    if not agent or not hasattr(agent, "config"):
        raise HTTPException(404, f"Agent not found: {agent_id}")

    plugin_config = {}
    if agent.config.plugins and agent.config.plugins.config:
        plugin_config = agent.config.plugins.config.get(plugin_name, {})

    return {"plugin": plugin_name, "agent": agent_id, "config": plugin_config}


@org_router.put("/{plugin_name}/config")
async def set_plugin_config(org_id: str, plugin_name: str, body: PluginConfigRequest):
    """Set plugin configuration for a specific agent."""
    org = _get_org_or_404(org_id)
    agent = org.agent_registry.get(body.agent_id)
    if not agent or not hasattr(agent, "config"):
        raise HTTPException(404, f"Agent not found: {body.agent_id}")

    if not agent.config.plugins:
        from axon.plugins.config import PluginsConfig
        agent.config.plugins = PluginsConfig()

    if not agent.config.plugins.config:
        agent.config.plugins.config = {}

    agent.config.plugins.config[plugin_name] = body.config

    # Persist to agent.yaml
    _persist_plugin_config_data(agent, plugin_name, body.config)

    # Rebuild plugin executor with new config
    _rebuild_agent_plugins(agent)

    return {"status": "configured", "plugin": plugin_name, "agent": body.agent_id, "config": body.config}


# ---------------------------------------------------------------------------
# Create / Update / Delete
# ---------------------------------------------------------------------------

@org_router.post("")
async def create_plugin(org_id: str, body: PluginCreateRequest):
    """Create a new external plugin on disk and register it."""
    _get_org_or_404(org_id)

    if not SNAKE_CASE_RE.match(body.name):
        raise HTTPException(400, "Plugin name must be snake_case (lowercase letters, digits, underscores)")
    if body.name in PLUGIN_REGISTRY:
        raise HTTPException(409, f"Plugin already exists: {body.name}")

    plugin_dir = _get_plugin_dir(org_id, body.name)
    plugin_dir.mkdir(parents=True, exist_ok=True)

    # Write plugin.yaml
    manifest_data = body.model_dump(exclude={"name"})
    manifest_data["name"] = body.name
    with open(plugin_dir / "plugin.yaml", "w", encoding="utf-8") as f:
        yaml.dump(manifest_data, f, default_flow_style=False, sort_keys=False)

    # Write scaffold __init__.py
    with open(plugin_dir / "__init__.py", "w", encoding="utf-8") as f:
        f.write(PLUGIN_SCAFFOLD)

    # Load and register
    cls = load_plugin_from_directory(plugin_dir)
    if not cls:
        shutil.rmtree(plugin_dir, ignore_errors=True)
        raise HTTPException(500, "Failed to load plugin after creation")

    logger.info("Created plugin: %s in %s", body.name, plugin_dir)
    return await get_plugin_detail(org_id, body.name)


@org_router.put("/{plugin_name}")
async def update_plugin(org_id: str, plugin_name: str, body: PluginUpdateRequest):
    """Update an external plugin's manifest."""
    _get_org_or_404(org_id)

    if plugin_name not in PLUGIN_REGISTRY:
        raise HTTPException(404, f"Plugin not found: {plugin_name}")
    if PLUGIN_SOURCE.get(plugin_name, "builtin") == "builtin":
        raise HTTPException(403, "Cannot edit built-in plugins")

    plugin_dir = _get_plugin_dir(org_id, plugin_name)
    manifest_path = plugin_dir / "plugin.yaml"
    if not manifest_path.exists():
        raise HTTPException(404, f"Plugin manifest not found on disk: {plugin_name}")

    # Read, merge, write
    with open(manifest_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    updates = body.model_dump(exclude_none=True)
    data.update(updates)

    with open(manifest_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    # Re-register: unregister old, reload from disk
    unregister_plugin(plugin_name)
    cls = load_plugin_from_directory(plugin_dir)
    if not cls:
        raise HTTPException(500, "Failed to reload plugin after update")

    logger.info("Updated plugin: %s", plugin_name)
    return await get_plugin_detail(org_id, plugin_name)


@org_router.delete("/{plugin_name}")
async def delete_plugin(org_id: str, plugin_name: str):
    """Delete an external plugin from disk and registry."""
    org = _get_org_or_404(org_id)

    if plugin_name not in PLUGIN_REGISTRY:
        raise HTTPException(404, f"Plugin not found: {plugin_name}")
    if PLUGIN_SOURCE.get(plugin_name, "builtin") == "builtin":
        raise HTTPException(403, "Cannot delete built-in plugins")

    # Disable from all agents first
    agents_affected = _disable_plugin_for_all(org, plugin_name)

    # Remove from registry
    unregister_plugin(plugin_name)

    # Delete from disk
    plugin_dir = _get_plugin_dir(org_id, plugin_name)
    if plugin_dir.exists():
        shutil.rmtree(plugin_dir)

    logger.info("Deleted plugin: %s (affected agents: %s)", plugin_name, agents_affected)
    return {"deleted": plugin_name, "agents_affected": agents_affected}

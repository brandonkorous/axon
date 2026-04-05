"""Plugin instance CRUD — org-level named plugin environments."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from axon.config import settings
from axon.logging import get_logger
from axon.plugins.instance import PluginInstanceConfig
from axon.plugins.registry import PLUGIN_REGISTRY
import axon.registry as registry

logger = get_logger(__name__)

org_router = APIRouter()

SLUG_RE = re.compile(r"^[a-z][a-z0-9-]*$")


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class InstanceCreateRequest(BaseModel):
    id: str
    name: str = ""
    agents: list[str] = Field(default_factory=list)
    config: dict[str, Any] = Field(default_factory=dict)


class InstanceUpdateRequest(BaseModel):
    name: str | None = None
    agents: list[str] | None = None
    config: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_org_or_404(org_id: str):
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Org not found: {org_id}")
    return org


def _persist_instances(org_id: str, instances: list[PluginInstanceConfig]) -> None:
    """Write plugin_instances to org.yaml."""
    org_dir = Path(settings.axon_orgs_dir) / org_id
    yaml_path = org_dir / "org.yaml"
    data: dict[str, Any] = {}
    if yaml_path.exists():
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    data["plugin_instances"] = [inst.model_dump() for inst in instances]
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def _rebuild_affected_agents(org, agent_ids: list[str]) -> None:
    """Rebuild plugin executors for all affected agents."""
    for aid in agent_ids:
        agent = org.agent_registry.get(aid)
        if agent and hasattr(agent, "_build_plugin_executor"):
            agent._plugin_executor = agent._build_plugin_executor()
            if agent._plugin_executor:
                agent.tool_executor._plugin_executor = agent._plugin_executor
            else:
                agent.tool_executor._plugin_executor = None
            agent.tools = agent._build_tool_list()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@org_router.get("/{plugin_name}/instances")
async def list_instances(org_id: str, plugin_name: str):
    """List all instances of a plugin."""
    org = _get_org_or_404(org_id)
    instances = [
        i.model_dump() for i in org.config.plugin_instances
        if i.plugin == plugin_name
    ]
    return {"instances": instances}


@org_router.post("/{plugin_name}/instances")
async def create_instance(
    org_id: str, plugin_name: str, body: InstanceCreateRequest,
):
    """Create a new plugin instance."""
    org = _get_org_or_404(org_id)
    if plugin_name not in PLUGIN_REGISTRY:
        raise HTTPException(404, f"Plugin not found: {plugin_name}")
    if not SLUG_RE.match(body.id):
        raise HTTPException(400, "ID must be lowercase alphanumeric with hyphens")
    if any(i.id == body.id for i in org.config.plugin_instances):
        raise HTTPException(409, f"Instance '{body.id}' already exists")

    inst = PluginInstanceConfig(
        id=body.id,
        plugin=plugin_name,
        name=body.name or body.id.replace("-", " ").title(),
        agents=body.agents,
        config=body.config,
    )
    org.config.plugin_instances.append(inst)
    _persist_instances(org_id, org.config.plugin_instances)
    _rebuild_affected_agents(org, body.agents)
    return inst.model_dump()


@org_router.put("/{plugin_name}/instances/{instance_id}")
async def update_instance(
    org_id: str, plugin_name: str, instance_id: str,
    body: InstanceUpdateRequest,
):
    """Update an existing plugin instance."""
    org = _get_org_or_404(org_id)
    inst = next(
        (i for i in org.config.plugin_instances if i.id == instance_id and i.plugin == plugin_name),
        None,
    )
    if not inst:
        raise HTTPException(404, f"Instance not found: {instance_id}")

    old_agents = set(inst.agents)

    if body.name is not None:
        inst.name = body.name
    if body.agents is not None:
        inst.agents = body.agents
    if body.config is not None:
        inst.config = body.config

    _persist_instances(org_id, org.config.plugin_instances)

    # Rebuild for agents added or removed
    affected = list(old_agents | set(inst.agents))
    _rebuild_affected_agents(org, affected)
    return inst.model_dump()


@org_router.delete("/{plugin_name}/instances/{instance_id}")
async def delete_instance(org_id: str, plugin_name: str, instance_id: str):
    """Delete a plugin instance."""
    org = _get_org_or_404(org_id)
    inst = next(
        (i for i in org.config.plugin_instances if i.id == instance_id and i.plugin == plugin_name),
        None,
    )
    if not inst:
        raise HTTPException(404, f"Instance not found: {instance_id}")

    agents_to_rebuild = list(inst.agents)
    org.config.plugin_instances = [
        i for i in org.config.plugin_instances if i.id != instance_id
    ]
    _persist_instances(org_id, org.config.plugin_instances)
    _rebuild_affected_agents(org, agents_to_rebuild)
    return {"deleted": instance_id}

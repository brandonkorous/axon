"""Integration management routes — list, enable, disable integrations."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from axon.integrations.registry import INTEGRATION_REGISTRY
from axon.logging import get_logger
import axon.registry as registry

logger = get_logger(__name__)

org_router = APIRouter()


@org_router.get("")
async def list_integrations(org_id: str):
    """List all registered integrations with per-agent status."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Organization not found: {org_id}")

    integrations = []
    for name, cls in sorted(INTEGRATION_REGISTRY.items()):
        instance = cls()
        enabled_by: list[str] = []
        for agent_id, agent in org.agent_registry.items():
            if name in getattr(agent.config, "integrations", _EMPTY).enabled:
                enabled_by.append(agent_id)

        integrations.append({
            "name": name,
            "description": instance.description,
            "required_scopes": instance.required_scopes,
            "tool_prefix": instance.tool_prefix,
            "tool_count": len(instance.get_tools()),
            "enabled_by": enabled_by,
        })

    return integrations


@org_router.get("/{name}")
async def get_integration_detail(org_id: str, name: str):
    """Get details for a specific integration."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Organization not found: {org_id}")

    cls = INTEGRATION_REGISTRY.get(name)
    if not cls:
        raise HTTPException(404, f"Integration not found: {name}")

    instance = cls()
    enabled_by: list[str] = []
    for agent_id, agent in org.agent_registry.items():
        if name in getattr(agent.config, "integrations", _EMPTY).enabled:
            enabled_by.append(agent_id)

    tools = [
        {
            "name": t["function"]["name"],
            "description": t["function"].get("description", ""),
        }
        for t in instance.get_tools()
    ]

    return {
        "name": name,
        "description": instance.description,
        "required_scopes": instance.required_scopes,
        "tool_prefix": instance.tool_prefix,
        "tools": tools,
        "enabled_by": enabled_by,
    }


@org_router.get("/agents/{agent_id}")
async def list_agent_integrations(org_id: str, agent_id: str):
    """List integrations enabled for a specific agent."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Organization not found: {org_id}")

    agent = org.agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(404, f"Agent not found: {agent_id}")

    enabled = getattr(agent.config, "integrations", _EMPTY).enabled
    result = []
    for name in enabled:
        cls = INTEGRATION_REGISTRY.get(name)
        if cls:
            instance = cls()
            result.append({
                "name": name,
                "description": instance.description,
                "tool_count": len(instance.get_tools()),
            })
        else:
            result.append({
                "name": name,
                "description": "(not registered)",
                "tool_count": 0,
            })

    return result


@org_router.post("/agents/{agent_id}/{name}/enable")
async def enable_integration(org_id: str, agent_id: str, name: str):
    """Enable an integration for an agent."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Organization not found: {org_id}")

    agent = org.agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(404, f"Agent not found: {agent_id}")

    if name not in INTEGRATION_REGISTRY:
        raise HTTPException(404, f"Integration not found: {name}")

    enabled = agent.config.integrations.enabled
    if name not in enabled:
        enabled.append(name)
        _rebuild_agent_integrations(agent)
        logger.info("Enabled integration %s for agent %s", name, agent_id)

    return {"status": "enabled", "agent_id": agent_id, "integration": name}


@org_router.post("/agents/{agent_id}/{name}/disable")
async def disable_integration(org_id: str, agent_id: str, name: str):
    """Disable an integration for an agent."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Organization not found: {org_id}")

    agent = org.agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(404, f"Agent not found: {agent_id}")

    enabled = agent.config.integrations.enabled
    if name in enabled:
        enabled.remove(name)
        _rebuild_agent_integrations(agent)
        logger.info("Disabled integration %s for agent %s", name, agent_id)

    return {"status": "disabled", "agent_id": agent_id, "integration": name}


@org_router.get("/{name}/status")
async def integration_status(org_id: str, name: str):
    """Health check — are credentials configured for this integration?"""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Organization not found: {org_id}")

    cls = INTEGRATION_REGISTRY.get(name)
    if not cls:
        raise HTTPException(404, f"Integration not found: {name}")

    # Check if credentials exist for this integration
    from axon.integrations.credentials import load_integration_credentials
    creds = await load_integration_credentials(org_id, [name])
    has_credentials = name in creds and bool(creds[name].get("access_token"))

    return {
        "name": name,
        "registered": True,
        "credentials_configured": has_credentials,
    }


def _rebuild_agent_integrations(agent) -> None:
    """Rebuild integration executor and tools after enable/disable."""
    from axon.integrations.registry import create_integration_executor
    enabled = agent.config.integrations.enabled
    agent._integration_executor = create_integration_executor(enabled) if enabled else None
    agent.tool_executor._integration_executor = agent._integration_executor
    agent.tools = agent._build_tool_list()


class _EmptyIntegrationConfig:
    """Fallback for agents without integration config."""
    enabled: list[str] = []


_EMPTY = _EmptyIntegrationConfig()

"""Agent management routes — list, status, CRUD, persona updates."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import axon.registry as registry
from axon.config import AgentType

logger = logging.getLogger(__name__)

router = APIRouter()
org_router = APIRouter()


class PersonaUpdateRequest(BaseModel):
    """Patchable persona fields."""

    name: str | None = None
    title: str | None = None
    tagline: str | None = None
    system_prompt: str | None = None
    color: str | None = None
    sparkle_color: str | None = None
    comms_enabled: bool | None = None
    email_alias: str | None = None


class ModelUpdateRequest(BaseModel):
    """Patchable model configuration fields."""

    reasoning: str | None = None
    navigator: str | None = None
    max_tokens: int | None = None
    temperature: float | None = None


class DelegationUpdateRequest(BaseModel):
    """Patchable delegation configuration."""

    can_delegate_to: list[str] | None = None
    accepts_from: list[str] | None = None


class LearningUpdateRequest(BaseModel):
    """Patchable learning configuration fields."""

    enabled: bool | None = None
    memory_model: str | None = None
    consolidation_interval: int | None = None
    confidence_decay_days: int | None = None
    max_recall_tokens: int | None = None


def _agent_email(agent, email_domain: str) -> str | None:
    """Build agent email address if comms is enabled and domain is set."""
    if email_domain and getattr(agent.config, "comms", None) and agent.config.comms.enabled:
        local_part = agent.config.comms.email_alias or agent.id
        return f"{local_part}@{email_domain}"
    return None


def _list_agents_for_registry(agent_reg: dict, email_domain: str = "") -> list[dict]:
    """Build agent list from a registry dict."""
    agents = []
    for agent_id, agent in agent_reg.items():
        agents.append({
            "id": agent.id,
            "name": agent.name,
            "title": agent.config.title,
            "tagline": agent.config.tagline,
            "ui": {
                "color": agent.config.ui.color,
                "avatar": agent.config.ui.avatar,
                "sparkle_color": agent.config.ui.sparkle_color,
            },
            "type": agent.config.type.value if hasattr(agent.config, "type") else "advisor",
            "model": agent.config.model.reasoning,
            "status": agent.lifecycle.status.value if hasattr(agent, "lifecycle") else "idle",
            "lifecycle": agent.lifecycle.to_dict() if hasattr(agent, "lifecycle") else None,
            "email": _agent_email(agent, email_domain),
            "comms_enabled": getattr(agent.config.comms, "enabled", False) if hasattr(agent.config, "comms") else False,
            "email_alias": getattr(agent.config.comms, "email_alias", "") if hasattr(agent.config, "comms") else "",
            "parent_id": agent.config.parent_id,
        })
    return agents


def _get_agent_detail(agent, email_domain: str = "") -> dict:
    """Build agent detail dict."""
    return {
        "id": agent.id,
        "name": agent.name,
        "title": agent.config.title,
        "tagline": agent.config.tagline,
        "ui": {
            "color": agent.config.ui.color,
            "avatar": agent.config.ui.avatar,
            "sparkle_color": agent.config.ui.sparkle_color,
        },
        "model": agent.config.model.reasoning,
        "vault": {
            "path": agent.config.vault.path,
            "root_file": agent.config.vault.root_file,
        },
        "delegation": {
            "can_delegate_to": agent.config.delegation.can_delegate_to,
            "accepts_from": agent.config.delegation.accepts_from,
        },
        "system_prompt": agent.system_prompt,
        "status": agent.lifecycle.status.value if hasattr(agent, "lifecycle") else "idle",
        "lifecycle": agent.lifecycle.to_dict() if hasattr(agent, "lifecycle") else None,
        "email": _agent_email(agent, email_domain),
        "parent_id": agent.config.parent_id,
    }


# ── Legacy routes (default org) ─────────────────────────────────────


@router.get("")
async def list_agents():
    """List all available agents with their status."""
    return {"agents": _list_agents_for_registry(registry.agent_registry)}


@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    """Get details for a specific agent."""
    agent = registry.agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return _get_agent_detail(agent)


# ── Org-scoped routes ───────────────────────────────────────────────


@org_router.get("")
async def list_org_agents(org_id: str):
    """List all agents in an organization."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization not found: {org_id}")
    email_domain = org.config.comms.email_domain if org.config.comms else ""
    return {"agents": _list_agents_for_registry(org.agent_registry, email_domain)}


@org_router.get("/{agent_id}")
async def get_org_agent(org_id: str, agent_id: str):
    """Get details for a specific agent in an organization."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization not found: {org_id}")
    agent = org.agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id} in org {org_id}")
    email_domain = org.config.comms.email_domain if org.config.comms else ""
    return _get_agent_detail(agent, email_domain)


@org_router.patch("/{agent_id}")
async def update_agent_persona(org_id: str, agent_id: str, body: PersonaUpdateRequest):
    """Update an agent's persona — name, title, tagline, system prompt, colors."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail=f"Org not found: {org_id}")
    agent = org.agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    # Persist to agent.yaml
    agent_yaml_path = Path(agent.config.vault.path) / "agent.yaml"
    if not agent_yaml_path.exists():
        raise HTTPException(status_code=500, detail="agent.yaml not found")

    with open(agent_yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if body.name is not None:
        data["name"] = body.name
        agent.name = body.name
        agent.config.name = body.name
    if body.title is not None:
        data["title"] = body.title
        agent.config.title = body.title
    if body.tagline is not None:
        data["tagline"] = body.tagline
        agent.config.tagline = body.tagline
    if body.color is not None:
        data.setdefault("ui", {})["color"] = body.color
        agent.config.ui.color = body.color
    if body.sparkle_color is not None:
        data.setdefault("ui", {})["sparkle_color"] = body.sparkle_color
        agent.config.ui.sparkle_color = body.sparkle_color
    if body.system_prompt is not None:
        data["system_prompt"] = body.system_prompt
        agent.config.system_prompt = body.system_prompt
        # Clear cached prompt so it re-resolves from config
        agent._system_prompt = body.system_prompt
    if body.comms_enabled is not None:
        data.setdefault("comms", {})["enabled"] = body.comms_enabled
        agent.config.comms.enabled = body.comms_enabled
        # Rebuild tools and executor so comms tools appear/disappear
        if hasattr(agent, "_rebuild_comms"):
            agent._rebuild_comms(org.config.comms)
    if body.email_alias is not None:
        data.setdefault("comms", {})["email_alias"] = body.email_alias
        agent.config.comms.email_alias = body.email_alias
        # Rebuild comms so the executor picks up the new alias
        if hasattr(agent, "_rebuild_comms"):
            agent._rebuild_comms(org.config.comms)
    with open(agent_yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    # Refresh orchestrator roster so name/title changes propagate
    _refresh_orchestrator_roster(org)

    logger.info("Agent '%s' persona updated in org '%s'", agent_id, org_id)
    email_domain = org.config.comms.email_domain if org.config.comms else ""
    return _get_agent_detail(agent, email_domain)


def _get_agent_or_404(org_id: str, agent_id: str):
    """Resolve org + agent, raising 404 on miss."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail=f"Org not found: {org_id}")
    agent = org.agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return org, agent


def _load_agent_yaml(agent) -> tuple[Path, dict]:
    """Load and return (path, data) for an agent's YAML file."""
    yaml_path = Path(agent.config.vault.path) / "agent.yaml"
    if not yaml_path.exists():
        raise HTTPException(status_code=500, detail="agent.yaml not found")
    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return yaml_path, data


def _save_agent_yaml(yaml_path: Path, data: dict) -> None:
    """Persist agent YAML data."""
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


# ── Model config endpoints ─────────────────────────────────────────


@org_router.get("/{agent_id}/model")
async def get_agent_model(org_id: str, agent_id: str):
    """Get an agent's model configuration."""
    _, agent = _get_agent_or_404(org_id, agent_id)
    return {
        "reasoning": agent.config.model.reasoning,
        "navigator": agent.config.model.navigator,
        "max_tokens": agent.config.model.max_tokens,
        "temperature": agent.config.model.temperature,
    }


@org_router.patch("/{agent_id}/model")
async def update_agent_model(org_id: str, agent_id: str, body: ModelUpdateRequest):
    """Update an agent's model configuration."""
    _, agent = _get_agent_or_404(org_id, agent_id)
    yaml_path, data = _load_agent_yaml(agent)
    model_data = data.setdefault("model", {})

    if body.reasoning is not None:
        model_data["reasoning"] = body.reasoning
        agent.config.model.reasoning = body.reasoning
    if body.navigator is not None:
        model_data["navigator"] = body.navigator
        agent.config.model.navigator = body.navigator
    if body.max_tokens is not None:
        model_data["max_tokens"] = body.max_tokens
        agent.config.model.max_tokens = body.max_tokens
    if body.temperature is not None:
        model_data["temperature"] = body.temperature
        agent.config.model.temperature = body.temperature

    _save_agent_yaml(yaml_path, data)
    logger.info("Agent '%s' model config updated in org '%s'", agent_id, org_id)
    return {"ok": True}


# ── Delegation config endpoints ────────────────────────────────────


@org_router.get("/{agent_id}/delegation")
async def get_agent_delegation(org_id: str, agent_id: str):
    """Get an agent's delegation configuration."""
    _, agent = _get_agent_or_404(org_id, agent_id)
    return {
        "can_delegate_to": agent.config.delegation.can_delegate_to,
        "accepts_from": agent.config.delegation.accepts_from,
    }


@org_router.patch("/{agent_id}/delegation")
async def update_agent_delegation(org_id: str, agent_id: str, body: DelegationUpdateRequest):
    """Update an agent's delegation configuration."""
    _, agent = _get_agent_or_404(org_id, agent_id)
    yaml_path, data = _load_agent_yaml(agent)
    deleg_data = data.setdefault("delegation", {})

    if body.can_delegate_to is not None:
        deleg_data["can_delegate_to"] = body.can_delegate_to
        agent.config.delegation.can_delegate_to = body.can_delegate_to
    if body.accepts_from is not None:
        deleg_data["accepts_from"] = body.accepts_from
        agent.config.delegation.accepts_from = body.accepts_from

    _save_agent_yaml(yaml_path, data)
    logger.info("Agent '%s' delegation updated in org '%s'", agent_id, org_id)
    return {"ok": True}


# ── Learning config endpoints ──────────────────────────────────────


@org_router.get("/{agent_id}/learning")
async def get_agent_learning(org_id: str, agent_id: str):
    """Get an agent's learning configuration."""
    _, agent = _get_agent_or_404(org_id, agent_id)
    lc = agent.config.learning
    return {
        "enabled": lc.enabled,
        "memory_model": lc.memory_model,
        "consolidation_interval": lc.consolidation_interval,
        "confidence_decay_days": lc.confidence_decay_days,
        "max_recall_tokens": lc.max_recall_tokens,
    }


@org_router.patch("/{agent_id}/learning")
async def update_agent_learning(org_id: str, agent_id: str, body: LearningUpdateRequest):
    """Update an agent's learning configuration."""
    _, agent = _get_agent_or_404(org_id, agent_id)
    yaml_path, data = _load_agent_yaml(agent)
    learn_data = data.setdefault("learning", {})

    if body.enabled is not None:
        learn_data["enabled"] = body.enabled
        agent.config.learning.enabled = body.enabled
    if body.memory_model is not None:
        learn_data["memory_model"] = body.memory_model
        agent.config.learning.memory_model = body.memory_model
    if body.consolidation_interval is not None:
        learn_data["consolidation_interval"] = body.consolidation_interval
        agent.config.learning.consolidation_interval = body.consolidation_interval
    if body.confidence_decay_days is not None:
        learn_data["confidence_decay_days"] = body.confidence_decay_days
        agent.config.learning.confidence_decay_days = body.confidence_decay_days
    if body.max_recall_tokens is not None:
        learn_data["max_recall_tokens"] = body.max_recall_tokens
        agent.config.learning.max_recall_tokens = body.max_recall_tokens

    _save_agent_yaml(yaml_path, data)
    logger.info("Agent '%s' learning config updated in org '%s'", agent_id, org_id)
    return {"ok": True}


def _refresh_orchestrator_roster(org) -> None:
    """Update orchestrator and huddle with the current specialist roster."""
    from axon.agents.axon_agent import AxonAgent

    specialists = {}
    for aid, agent in org.agent_registry.items():
        if hasattr(agent, "config") and agent.config.type == AgentType.ADVISOR and not agent.config.parent_id:
            specialists[aid] = agent.config

    for agent in org.agent_registry.values():
        if isinstance(agent, AxonAgent):
            agent.available_agents = specialists
            agent._update_system_prompt()

    if org.huddle:
        advisor_agents = {
            aid: org.agent_registry[aid] for aid in specialists
            if aid in org.agent_registry
        }
        org.huddle.refresh_advisors(specialists, advisor_agents=advisor_agents)

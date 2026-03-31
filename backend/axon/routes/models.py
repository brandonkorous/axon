"""Model management routes — registry, role assignments, Ollama discovery."""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import axon.registry as registry
from axon.config import settings
from axon.org import OrgModelConfig, ModelRoleAssignments, RegisteredModel

logger = logging.getLogger(__name__)

org_router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_org_or_404(org_id: str):
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Org not found: {org_id}")
    return org


def _persist_model_config(org_id: str, model_config: OrgModelConfig) -> None:
    """Write models section back to org.yaml."""
    yaml_path = Path(settings.axon_orgs_dir) / org_id / "org.yaml"
    if not yaml_path.exists():
        return
    try:
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        data["models"] = model_config.model_dump(mode="json")

        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    except Exception:
        logger.warning("Failed to persist model config for org %s", org_id)


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class RegisterModelRequest(BaseModel):
    id: str
    provider: str = ""
    display_name: str = ""
    model_type: str = "cloud"


class UpdateRolesRequest(BaseModel):
    navigator: str = ""
    reasoning: str = ""
    memory: str = ""
    agent: str = ""


# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------

@org_router.get("")
async def list_models(org_id: str):
    """List registered models and current role assignments."""
    org = _get_org_or_404(org_id)
    mc = org.config.models
    return {
        "registered_models": [m.model_dump() for m in mc.registered_models],
        "roles": mc.roles.model_dump(),
    }


@org_router.post("")
async def register_model(org_id: str, body: RegisterModelRequest):
    """Register a new model for use in this org."""
    org = _get_org_or_404(org_id)
    mc = org.config.models

    # Check for duplicate
    if any(m.id == body.id for m in mc.registered_models):
        raise HTTPException(409, f"Model already registered: {body.id}")

    # Auto-detect provider from model ID prefix
    provider = body.provider
    if not provider:
        if body.id.startswith("ollama/"):
            provider = "ollama"
        elif body.id.startswith("anthropic/"):
            provider = "anthropic"
        elif body.id.startswith("openai/"):
            provider = "openai"

    model = RegisteredModel(
        id=body.id,
        provider=provider,
        display_name=body.display_name or body.id.split("/")[-1],
        model_type=body.model_type,
    )
    mc.registered_models.append(model)
    _persist_model_config(org_id, mc)

    return {"status": "registered", "model": model.model_dump()}


@org_router.delete("/{model_id:path}")
async def unregister_model(org_id: str, model_id: str):
    """Unregister a model from this org."""
    org = _get_org_or_404(org_id)
    mc = org.config.models

    before = len(mc.registered_models)
    mc.registered_models = [m for m in mc.registered_models if m.id != model_id]

    if len(mc.registered_models) == before:
        raise HTTPException(404, f"Model not found: {model_id}")

    # Clear any role assignments pointing to this model
    roles = mc.roles
    if roles.navigator == model_id:
        roles.navigator = ""
    if roles.reasoning == model_id:
        roles.reasoning = ""
    if roles.memory == model_id:
        roles.memory = ""
    if roles.agent == model_id:
        roles.agent = ""

    _persist_model_config(org_id, mc)
    return {"status": "unregistered", "model_id": model_id}


# ---------------------------------------------------------------------------
# Role assignments
# ---------------------------------------------------------------------------

@org_router.get("/roles")
async def get_roles(org_id: str):
    """Get current role assignments."""
    org = _get_org_or_404(org_id)
    return {"roles": org.config.models.roles.model_dump()}


@org_router.put("/roles")
async def update_roles(org_id: str, body: UpdateRolesRequest):
    """Update role assignments."""
    org = _get_org_or_404(org_id)
    mc = org.config.models

    registered_ids = {m.id for m in mc.registered_models}

    # Validate that assigned models are registered (empty string is allowed)
    for role_name in ("navigator", "reasoning", "memory", "agent"):
        model_id = getattr(body, role_name)
        if model_id and model_id not in registered_ids:
            raise HTTPException(
                400, f"Model '{model_id}' is not registered. Register it first.",
            )

    mc.roles = ModelRoleAssignments(**body.model_dump())
    _persist_model_config(org_id, mc)

    # Propagate new model roles to all running agents immediately
    roles = mc.roles
    for agent_id, agent in org.agent_registry.items():
        if not hasattr(agent, "config"):
            continue
        # Read agent YAML to check for per-agent overrides
        yaml_path = Path(agent.config.vault.path) / "agent.yaml"
        agent_yaml_model = {}
        if yaml_path.exists():
            try:
                with open(yaml_path, encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                agent_yaml_model = data.get("model", {})
            except Exception:
                pass
        # Only update if the agent doesn't have a per-agent override
        if roles.reasoning and not agent_yaml_model.get("reasoning"):
            agent.config.model.reasoning = roles.reasoning
        if roles.navigator and not agent_yaml_model.get("navigator"):
            agent.config.model.navigator = roles.navigator
        logger.info(
            "[MODELS] Propagated roles to %s: reasoning=%s, navigator=%s",
            agent_id, agent.config.model.reasoning, agent.config.model.navigator,
        )

    return {"status": "updated", "roles": mc.roles.model_dump()}


# ---------------------------------------------------------------------------
# Model catalog
# ---------------------------------------------------------------------------

CURATED_MODELS = {
    "anthropic": {
        "name": "Anthropic",
        "requires_key": True,
        "models": [
            ("anthropic/claude-opus-4-20250514", "Claude Opus 4", "Most capable, deep reasoning", "premium"),
            ("anthropic/claude-sonnet-4-20250514", "Claude Sonnet 4", "Fast and capable, great balance", "recommended"),
            ("anthropic/claude-haiku-4-5-20251001", "Claude Haiku 4.5", "Fastest, most affordable", "budget"),
        ],
    },
    "openai": {
        "name": "OpenAI",
        "requires_key": True,
        "models": [
            ("openai/gpt-4o", "GPT-4o", "Fast multimodal model", "recommended"),
            ("openai/gpt-4o-mini", "GPT-4o Mini", "Affordable and fast", "budget"),
            ("openai/o3", "o3", "Advanced reasoning", "premium"),
            ("openai/o3-mini", "o3 Mini", "Reasoning, more affordable", "recommended"),
        ],
    },
    "deepseek": {
        "name": "DeepSeek",
        "requires_key": True,
        "models": [
            ("deepseek/deepseek-chat", "DeepSeek Chat", "Strong general purpose", "budget"),
            ("deepseek/deepseek-reasoner", "DeepSeek Reasoner", "Advanced reasoning", "recommended"),
        ],
    },
    "google": {
        "name": "Google",
        "requires_key": True,
        "models": [
            ("gemini/gemini-2.5-pro", "Gemini 2.5 Pro", "Google's most capable", "premium"),
            ("gemini/gemini-2.5-flash", "Gemini 2.5 Flash", "Fast and affordable", "budget"),
        ],
    },
    "groq": {
        "name": "Groq",
        "requires_key": True,
        "models": [
            ("groq/llama-3.3-70b-versatile", "Llama 3.3 70B", "Fast inference via Groq", "recommended"),
            ("groq/llama-3.1-8b-instant", "Llama 3.1 8B", "Ultra-fast, lightweight", "budget"),
        ],
    },
    "xai": {
        "name": "xAI",
        "requires_key": True,
        "models": [
            ("xai/grok-3", "Grok 3", "xAI's most capable", "premium"),
            ("xai/grok-3-mini", "Grok 3 Mini", "Fast and affordable", "budget"),
        ],
    },
}


def _build_catalog() -> dict:
    """Build curated model catalog grouped by provider."""
    providers = []
    for provider_id, info in CURATED_MODELS.items():
        models = []
        for model_id, name, description, tier in info["models"]:
            models.append({
                "id": model_id,
                "name": name,
                "description": description,
                "tier": tier,
            })
        providers.append({
            "id": provider_id,
            "name": info["name"],
            "requires_key": info["requires_key"],
            "models": models,
        })
    return {"providers": providers}


@org_router.get("/catalog")
async def get_model_catalog(org_id: str):
    """Return a curated list of available models grouped by provider."""
    _get_org_or_404(org_id)
    return await asyncio.to_thread(_build_catalog)


# ---------------------------------------------------------------------------
# Ollama discovery
# ---------------------------------------------------------------------------

async def _discover_ollama_models() -> list[dict]:
    """Discover models available in Ollama."""
    import httpx

    ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434")
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{ollama_url}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                return [
                    {
                        "id": f"ollama/{m['name']}",
                        "name": m["name"],
                        "size": m.get("size", 0),
                    }
                    for m in data.get("models", [])
                ]
    except Exception:
        pass
    return []


@org_router.get("/discover")
async def discover_models(org_id: str):
    """Auto-detect available Ollama models."""
    _get_org_or_404(org_id)
    models = await _discover_ollama_models()
    return {"provider": "ollama", "models": models}


# ---------------------------------------------------------------------------
# Status (onboarding check)
# ---------------------------------------------------------------------------

@org_router.get("/status")
async def model_status(org_id: str):
    """Check if the org has models configured (useful for onboarding modal)."""
    org = _get_org_or_404(org_id)
    mc = org.config.models
    has_models = len(mc.registered_models) > 0
    has_roles = bool(mc.roles.agent or mc.roles.reasoning or mc.roles.navigator)
    return {
        "configured": has_models and has_roles,
        "registered_count": len(mc.registered_models),
        "roles_assigned": has_roles,
    }

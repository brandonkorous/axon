"""Recruitment routes — list pending requests, approve/deny, create agents."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import axon.registry as registry
from axon.config import AgentType, PersonaConfig, _load_agent_yaml, settings
from axon.org import ensure_huddle
from axon.vault.scaffold import scaffold_vault

logger = logging.getLogger(__name__)

org_router = APIRouter()


class ApproveRequest(BaseModel):
    name: str  # Agent display name (e.g., "Alex")
    agent_id: str = ""  # Slug ID (derived from name if empty)
    template: str = "advisor"  # Vault template to scaffold from
    title: str = ""  # Full title (e.g., "Design Lead")
    title_tag: str = ""  # Short tag, up to 4 chars (e.g., "DSGN")
    tagline: str = ""  # One-line description
    color: str = "#6B7280"
    sparkle_color: str = "#9CA3AF"
    parent_id: str = ""  # If set, creates a sub-agent under this parent
    system_prompt: str = ""  # Custom instructions (overwrites template instructions.md)
    domains: list[str] = []  # Advisory domains (written to agent.yaml guardrails)


class DeclineRequest(BaseModel):
    reason: str = ""


@org_router.get("/pending")
async def list_pending_recruitment(org_id: str):
    """List pending recruitment requests from shared vault."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail=f"Org not found: {org_id}")
    if not org.shared_vault:
        return {"requests": []}

    requests = []
    try:
        files = org.shared_vault.list_branch("tasks")
    except FileNotFoundError:
        return {"requests": []}

    for f in files:
        if not f.get("name", "").startswith("recruit-") and "recruit" not in f.get("path", ""):
            continue
        try:
            meta, body = org.shared_vault.read_file(f["path"])
            if meta.get("type") != "recruitment":
                continue
            if meta.get("status") != "awaiting_approval":
                continue
            requests.append({
                "task_path": f["path"],
                "role": meta.get("role", ""),
                "reason": meta.get("reason", ""),
                "requested_by": meta.get("requested_by", ""),
                "system_prompt": meta.get("system_prompt", ""),
                "domains": meta.get("domains", []),
                "suggested_capabilities": meta.get("suggested_capabilities", []),
                "created_at": meta.get("created_at", ""),
            })
        except Exception:
            continue

    return {"requests": requests}


@org_router.post("/{task_path:path}/approve")
async def approve_recruitment(org_id: str, task_path: str, body: ApproveRequest):
    """Approve a recruitment request — scaffolds vault and hot-loads agent."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail=f"Org not found: {org_id}")

    # Find the org directory
    orgs_dir = settings.axon_orgs_dir
    if not orgs_dir:
        raise HTTPException(status_code=500, detail="Multi-org mode required")
    org_dir = Path(orgs_dir) / org_id
    vaults_dir = org_dir / "vaults"

    # Derive agent_id from name
    agent_id = body.agent_id or body.name.lower().replace(" ", "_")

    # Check for duplicates
    if agent_id in org.agent_registry:
        raise HTTPException(status_code=409, detail=f"Agent '{agent_id}' already exists")

    # Scaffold vault from template
    vault_path = vaults_dir / agent_id
    try:
        scaffold_vault(
            vault_path,
            template=body.template,
            agent_name=body.name,
            agent_title=body.title or body.name,
            agent_id=agent_id,
            agent_tagline=body.tagline or body.name,
        )
    except FileExistsError:
        raise HTTPException(status_code=409, detail=f"Vault already exists: {agent_id}")

    # Override all persona fields in scaffolded agent.yaml
    agent_yaml_path = vault_path / "agent.yaml"
    if agent_yaml_path.exists():
        with open(agent_yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        data["name"] = body.name
        if body.title:
            data["title"] = body.title
        if body.title_tag:
            data["title_tag"] = body.title_tag[:4]
        if body.tagline:
            data["tagline"] = body.tagline
        data.setdefault("ui", {})["color"] = body.color
        data.setdefault("ui", {})["sparkle_color"] = body.sparkle_color
        if body.parent_id:
            data["parent_id"] = body.parent_id
        if body.domains:
            data.setdefault("guardrails", {}).setdefault("domains", {})["allowed_domains"] = body.domains
        with open(agent_yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    # Write custom instructions if the requesting agent provided a system prompt.
    # All operational instructions (vault usage, action protocol, team building,
    # recruitment) are injected dynamically by _build_messages — instructions.md
    # only needs the role-specific content.
    if body.system_prompt:
        instructions_path = vault_path / "instructions.md"
        instructions_path.write_text(body.system_prompt, encoding="utf-8")

    # Hot-load the agent into the registry
    try:
        config = _load_agent_yaml(agent_yaml_path, vault_path)
        data_dir = str(org_dir / "data")

        from axon.agents.agent import Agent

        agent = Agent(
            config,
            data_dir=data_dir,
            shared_vault=org.shared_vault,
            audit_logger=org.audit_logger,
            org_id=org_id,
        )
        org.agent_registry[agent_id] = agent

        # Auto-wire parent delegation for sub-agents
        if config.parent_id:
            parent_agent = org.agent_registry.get(config.parent_id)
            if parent_agent and hasattr(parent_agent, "config"):
                if agent_id not in parent_agent.config.delegation.can_delegate_to and "*" not in parent_agent.config.delegation.can_delegate_to:
                    parent_agent.config.delegation.can_delegate_to.append(agent_id)
                    # Rebuild tool list so delegate_task becomes available
                    if hasattr(parent_agent, "_build_tool_list"):
                        parent_agent.tools = parent_agent._build_tool_list()

        # Update orchestrator's specialist roster
        _refresh_orchestrator_roster(org)

        # Rebuild peer rosters so existing agents discover the new teammate
        _rebuild_peer_rosters(org)

        # Auto-create huddle if this is the first advisor
        ensure_huddle(org, settings.axon_orgs_dir)

        logger.info("Agent '%s' created and loaded in org '%s'", agent_id, org_id)
    except Exception as e:
        logger.exception("Failed to hot-load agent '%s'", agent_id)
        raise HTTPException(status_code=500, detail=f"Agent scaffolded but failed to load: {e}")

    # Update the recruitment task status
    if org.shared_vault:
        try:
            meta, body_text = org.shared_vault.read_file(task_path)
            meta["status"] = "done"
            meta["approved_agent_id"] = agent_id
            org.shared_vault.write_file(task_path, meta, body_text)
        except Exception:
            pass  # Non-critical

    return {
        "status": "created",
        "agent_id": agent_id,
        "name": body.name,
        "vault_path": str(vault_path),
    }


@org_router.post("/{task_path:path}/decline")
async def decline_recruitment(org_id: str, task_path: str, body: DeclineRequest):
    """Decline a recruitment request."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail=f"Org not found: {org_id}")
    if not org.shared_vault:
        raise HTTPException(status_code=404, detail="No shared vault")

    try:
        meta, body_text = org.shared_vault.read_file(task_path)
        meta["status"] = "declined"
        if body.reason:
            meta["decline_reason"] = body.reason
        org.shared_vault.write_file(task_path, meta, body_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "declined", "task_path": task_path}


def _refresh_orchestrator_roster(org) -> None:
    """Update orchestrator and huddle with the current specialist roster."""
    from axon.agents.axon_agent import AxonAgent

    specialists = {}
    for aid, agent in org.agent_registry.items():
        if (
            hasattr(agent, "config")
            and agent.config.type == AgentType.ADVISOR
            and not agent.config.parent_id
        ):
            specialists[aid] = agent.config

    for agent in org.agent_registry.values():
        if isinstance(agent, AxonAgent):
            agent.available_agents = specialists
            agent._update_system_prompt()

    # Refresh huddle advisor roster + vault navigators + agent refs
    if org.huddle:
        advisor_agents = {
            aid: org.agent_registry[aid] for aid in specialists
            if aid in org.agent_registry
        }
        org.huddle.refresh_advisors(specialists, advisor_agents=advisor_agents)


def _rebuild_peer_rosters(org) -> None:
    """Rebuild peer rosters for all agents after a new agent is added."""
    from axon.agents.axon_agent import AxonAgent

    # Collect all configs from live agents
    all_configs = {
        aid: agent.config
        for aid, agent in org.agent_registry.items()
        if hasattr(agent, "config")
    }

    for agent in org.agent_registry.values():
        if isinstance(agent, AxonAgent):
            continue  # Orchestrator has its own roster
        if hasattr(agent, "build_roster"):
            agent.build_roster(all_configs)

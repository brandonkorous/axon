"""Worker setup routes — create, manage, and query external agents."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

import axon.registry as registry
from axon.config import AgentType, PersonaConfig, _load_agent_yaml, settings
from axon.runner_manager import runner_manager
from axon.runner_scaffold import scaffold_runner
from axon.vault.scaffold import scaffold_vault
from axon.worker_types import WorkerType

logger = logging.getLogger(__name__)

org_router = APIRouter()

HEARTBEAT_TIMEOUT = 60


class WorkerCreateRequest(BaseModel):
    name: str
    agent_id: str = ""
    codebase_path: str = ""
    worker_type: str = WorkerType.CODE
    accepts_from: list[str] = ["axon"]
    color: str = "#10B981"
    type_config: dict = {}


class WorkerUpdateRequest(BaseModel):
    name: str | None = None
    codebase_path: str | None = None
    accepts_from: list[str] | None = None
    color: str | None = None


def _worker_info(aid: str, agent, org_id: str) -> dict:
    """Build a worker info dict from an agent instance."""
    last_poll = getattr(agent, "last_poll_time", None)
    connected = False
    last_seen = None
    if last_poll:
        elapsed = (datetime.utcnow() - last_poll).total_seconds()
        connected = elapsed < HEARTBEAT_TIMEOUT
        last_seen = last_poll.isoformat() + "Z"

    codebase_path = ""
    accepts_from: list[str] = []
    color = "#10B981"
    worker_type = WorkerType.CODE
    agent_yaml = Path(agent.config.vault.path) / "agent.yaml"
    if agent_yaml.exists():
        with open(agent_yaml, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        worker_cfg = data.get("worker", {})
        codebase_path = worker_cfg.get("codebase_path", "")
        worker_type = worker_cfg.get("worker_type", WorkerType.CODE)
        accepts_from = data.get("delegation", {}).get("accepts_from", [])
        color = data.get("ui", {}).get("color", "#10B981")

    return {
        "agent_id": aid,
        "name": agent.name,
        "connected": connected,
        "last_seen": last_seen,
        "codebase_path": codebase_path,
        "worker_type": worker_type,
        "accepts_from": accepts_from,
        "color": color,
        "process_state": runner_manager.status(org_id, aid),
    }


@org_router.get("")
async def list_workers(org_id: str):
    """List all external/worker agents with connection status."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Org not found: {org_id}")

    workers = []
    for aid, agent in org.agent_registry.items():
        if not getattr(agent, "is_external", False):
            continue
        workers.append(_worker_info(aid, agent, org_id))

    return {"workers": workers}


@org_router.post("")
async def create_worker(org_id: str, body: WorkerCreateRequest, request: Request):
    """Create a new external/worker agent and scaffold its runner."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Org not found: {org_id}")

    # Validate worker type
    valid_types = [t.value for t in WorkerType]
    if body.worker_type not in valid_types:
        raise HTTPException(400, f"Invalid worker_type: {body.worker_type}. Must be one of: {valid_types}")

    orgs_dir = settings.axon_orgs_dir
    if not orgs_dir:
        raise HTTPException(500, "Multi-org mode required for worker setup")
    org_dir = Path(orgs_dir) / org_id
    vaults_dir = org_dir / "vaults"

    agent_id = body.agent_id or body.name.lower().replace(" ", "_")
    if agent_id in org.agent_registry:
        raise HTTPException(409, f"Agent '{agent_id}' already exists")

    # Scaffold vault from executor template
    vault_path = vaults_dir / agent_id
    tagline = f"{body.worker_type.capitalize()} worker"
    if body.codebase_path:
        tagline += f" for {body.codebase_path.replace(chr(92), '/')}"

    try:
        scaffold_vault(
            vault_path,
            template="executor",
            agent_name=body.name,
            agent_title=body.name,
            agent_id=agent_id,
            agent_tagline=tagline,
        )
    except FileExistsError:
        raise HTTPException(409, f"Vault already exists: {agent_id}")

    # Customize agent.yaml with worker-specific config
    agent_yaml_path = vault_path / "agent.yaml"
    if agent_yaml_path.exists():
        with open(agent_yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        data.setdefault("ui", {})["color"] = body.color
        data.setdefault("delegation", {})["accepts_from"] = body.accepts_from
        data["worker"] = {
            "codebase_path": body.codebase_path,
            "worker_type": body.worker_type,
        }
        with open(agent_yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    # Scaffold self-contained runner app
    runners_dir = org_dir / "runners"
    runners_dir.mkdir(parents=True, exist_ok=True)
    axon_url = _resolve_axon_url(request)
    try:
        scaffold_runner(
            runners_dir, agent_id, axon_url, org_id, body.codebase_path,
            worker_type=body.worker_type,
            type_config=body.type_config or None,
        )
    except FileExistsError:
        logger.warning("Runner dir already exists for '%s'", agent_id)

    # Hot-load agent into registry
    try:
        config = _load_agent_yaml(agent_yaml_path, vault_path)
        data_dir = str(org_dir / "data")

        from axon.agents.external_agent import ExternalAgent
        agent = ExternalAgent(
            config,
            data_dir=data_dir,
            shared_vault=org.shared_vault,
            audit_logger=org.audit_logger,
            org_id=org_id,
        )
        org.agent_registry[agent_id] = agent
        _refresh_orchestrator_roster(org)
        logger.info("Worker '%s' (%s) created in org '%s'", agent_id, body.worker_type, org_id)
    except Exception as e:
        logger.exception("Failed to hot-load worker '%s'", agent_id)
        raise HTTPException(500, f"Scaffolded but failed to load: {e}")

    return {
        "agent_id": agent_id,
        "name": body.name,
        "worker_type": body.worker_type,
        "vault_path": str(vault_path),
    }


@org_router.get("/{agent_id}")
async def get_worker(org_id: str, agent_id: str, request: Request):
    """Get full details for a worker agent."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Org not found: {org_id}")
    agent = org.agent_registry.get(agent_id)
    if not agent or not getattr(agent, "is_external", False):
        raise HTTPException(404, f"Worker not found: {agent_id}")

    return _worker_info(agent_id, agent, org_id)


@org_router.patch("/{agent_id}")
async def update_worker(org_id: str, agent_id: str, body: WorkerUpdateRequest):
    """Update a worker agent's config."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Org not found: {org_id}")
    agent = org.agent_registry.get(agent_id)
    if not agent or not getattr(agent, "is_external", False):
        raise HTTPException(404, f"Worker not found: {agent_id}")

    agent_yaml_path = Path(agent.config.vault.path) / "agent.yaml"
    if not agent_yaml_path.exists():
        raise HTTPException(500, "agent.yaml not found")

    with open(agent_yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if body.name is not None:
        data["name"] = body.name
        agent.name = body.name
        agent.config.name = body.name
    if body.codebase_path is not None:
        data.setdefault("worker", {})["codebase_path"] = body.codebase_path
    if body.accepts_from is not None:
        data.setdefault("delegation", {})["accepts_from"] = body.accepts_from
    if body.color is not None:
        data.setdefault("ui", {})["color"] = body.color

    with open(agent_yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    logger.info("Worker '%s' updated in org '%s'", agent_id, org_id)
    return _worker_info(agent_id, agent, org_id)


@org_router.delete("/{agent_id}")
async def delete_worker(org_id: str, agent_id: str):
    """Remove a worker agent from the registry and stop its runner."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Org not found: {org_id}")
    agent = org.agent_registry.get(agent_id)
    if not agent or not getattr(agent, "is_external", False):
        raise HTTPException(404, f"Worker not found: {agent_id}")

    await runner_manager.stop(org_id, agent_id)

    del org.agent_registry[agent_id]
    _refresh_orchestrator_roster(org)
    logger.info("Worker '%s' removed from org '%s'", agent_id, org_id)
    return {"status": "removed", "agent_id": agent_id}


# ── Helpers ───────────────────────────────────────────────────────

def _resolve_axon_url(request: Request) -> str:
    """Best-effort URL for the runner to connect to."""
    return f"{request.url.scheme}://{request.url.netloc}"


def _refresh_orchestrator_roster(org) -> None:
    from axon.agents.axon_agent import AxonAgent
    specialists = {}
    for aid, agent in org.agent_registry.items():
        if hasattr(agent, "config") and agent.config.type == AgentType.ADVISOR:
            specialists[aid] = agent.config
    for agent in org.agent_registry.values():
        if isinstance(agent, AxonAgent):
            agent.available_agents = specialists
            agent._update_system_prompt()
    # Refresh huddle advisor roster + vault navigators
    if org.huddle:
        org.huddle.refresh_advisors(specialists)

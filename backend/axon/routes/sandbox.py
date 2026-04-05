"""Sandbox management routes — status, logs, and lifecycle for sandbox containers."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from axon.logging import get_logger
import axon.registry as registry
from axon.sandbox.manager import sandbox_manager
from axon.sandbox.types import resolve_sandbox_type

logger = get_logger(__name__)

org_router = APIRouter()


class MountValidateRequest(BaseModel):
    path: str


@org_router.post("/validate-mount")
async def validate_mount(org_id: str, body: MountValidateRequest):
    """Validate a host mount path for safety."""
    from axon.sandbox.mount_validation import validate_mount_path
    from axon.config import settings

    axon_dirs = [settings.axon_orgs_dir]
    valid, error = validate_mount_path(body.path, axon_dirs)
    return {"valid": valid, "error": error if not valid else None}


@org_router.get("/status")
async def sandbox_availability():
    """Check if sandbox runtime is available."""
    available = await sandbox_manager.check_available()
    return {
        "available": available,
        "containers": len(sandbox_manager._containers),
    }


@org_router.get("/running")
async def list_running_instances(org_id: str):
    """List all running sandbox containers for this org."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Org not found: {org_id}")

    prefix = f"{org_id}/"
    running = []
    for key, sandbox_id in sandbox_manager._containers.items():
        if not key.startswith(prefix):
            continue
        parts = key.split("/", 2)
        instance_id = parts[2] if len(parts) > 2 else ""
        # Find the plugin instance config for display name
        inst_cfg = next(
            (i for i in org.config.plugin_instances if i.id == instance_id),
            None,
        )
        running.append({
            "instance_id": instance_id,
            "instance_name": inst_cfg.name if inst_cfg else instance_id,
            "plugin": inst_cfg.plugin if inst_cfg else "sandbox",
            "agents": inst_cfg.agents if inst_cfg else [],
            "sandbox_id": sandbox_id[:12],
            "status": "running",
        })
    return {"instances": running}


@org_router.post("/running/{instance_id}/stop")
async def stop_running_instance(org_id: str, instance_id: str):
    """Stop a running sandbox container by instance ID."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Org not found: {org_id}")

    # Find any key matching this instance_id
    target_key = None
    for key in sandbox_manager._containers:
        if key.startswith(f"{org_id}/") and key.endswith(f"/{instance_id}"):
            target_key = key
            break
    if not target_key:
        raise HTTPException(404, f"No running instance: {instance_id}")

    parts = target_key.split("/", 2)
    await sandbox_manager.destroy(parts[0], parts[1], parts[2])
    return {"stopped": instance_id}


@org_router.get("/{agent_id}")
async def sandbox_status(org_id: str, agent_id: str, instance_id: str | None = None):
    """Get sandbox container status for a worker."""
    _validate_worker(org_id, agent_id)
    return sandbox_manager.status(org_id, agent_id, instance_id)


@org_router.get("/{agent_id}/instances")
async def list_sandbox_instances(org_id: str, agent_id: str):
    """List all running sandbox instances for an agent."""
    _validate_worker(org_id, agent_id)
    return {"instances": sandbox_manager.list_instances(org_id, agent_id)}


@org_router.get("/{agent_id}/resolved-type")
async def resolved_sandbox_type(org_id: str, agent_id: str):
    """Resolve the minimum sandbox type based on agent's enabled plugins."""
    org = _validate_worker(org_id, agent_id)
    agent = org.agent_registry[agent_id]

    required_types: list[str] = []
    if hasattr(agent, "config") and hasattr(agent.config, "plugins") and agent.config.plugins:
        from axon.plugins.registry import PLUGIN_REGISTRY
        for plugin_name in agent.config.plugins.enabled:
            cls = PLUGIN_REGISTRY.get(plugin_name)
            if cls:
                instance = cls()
                if instance.manifest.sandbox_type:
                    required_types.append(instance.manifest.sandbox_type)

    resolved = resolve_sandbox_type(required_types)
    return {
        "resolved_type": resolved.value,
        "required_types": required_types,
    }


@org_router.get("/{agent_id}/logs")
async def sandbox_logs(
    org_id: str, agent_id: str,
    instance_id: str | None = None, tail: int = 100,
):
    """Get sandbox container logs."""
    _validate_worker(org_id, agent_id)
    lines = await sandbox_manager.get_logs_async(org_id, agent_id, instance_id, tail)
    return {"lines": lines}


@org_router.post("/{agent_id}/restart")
async def restart_sandbox(org_id: str, agent_id: str, instance_id: str | None = None):
    """Restart a sandbox container (stop + start)."""
    _validate_worker(org_id, agent_id)

    await sandbox_manager.stop(org_id, agent_id, instance_id)

    # Re-creation requires runner config — delegate to worker control
    return {"status": "stopped", "message": "Use worker start to recreate sandbox"}


@org_router.delete("/{agent_id}")
async def destroy_sandbox(org_id: str, agent_id: str, instance_id: str | None = None):
    """Force-remove a sandbox container."""
    _validate_worker(org_id, agent_id)
    await sandbox_manager.destroy(org_id, agent_id, instance_id)
    return {"status": "destroyed"}


def _validate_worker(org_id: str, agent_id: str):
    """Raise 404 if org or worker not found. Returns org instance."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Org not found: {org_id}")
    agent = org.agent_registry.get(agent_id)
    if not agent or not getattr(agent, "is_external", False):
        raise HTTPException(404, f"Worker not found: {agent_id}")
    return org

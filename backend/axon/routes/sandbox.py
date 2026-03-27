"""Sandbox management routes — status, logs, and lifecycle for sandbox containers."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

import axon.registry as registry
from axon.sandbox.manager import sandbox_manager

logger = logging.getLogger(__name__)

org_router = APIRouter()


@org_router.get("/status")
async def sandbox_availability():
    """Check if Docker sandbox support is available."""
    return {
        "available": sandbox_manager.available,
        "containers": len(sandbox_manager._containers),
    }


@org_router.get("/{agent_id}")
async def sandbox_status(org_id: str, agent_id: str):
    """Get sandbox container status for a worker."""
    _validate_worker(org_id, agent_id)
    return sandbox_manager.status(org_id, agent_id)


@org_router.get("/{agent_id}/logs")
async def sandbox_logs(org_id: str, agent_id: str, tail: int = 100):
    """Get sandbox container logs."""
    _validate_worker(org_id, agent_id)
    return {"lines": sandbox_manager.logs(org_id, agent_id, tail)}


@org_router.post("/{agent_id}/restart")
async def restart_sandbox(org_id: str, agent_id: str):
    """Restart a sandbox container (stop + start)."""
    _validate_worker(org_id, agent_id)

    await sandbox_manager.stop(org_id, agent_id)

    # Re-creation requires runner config — delegate to worker control
    return {"status": "stopped", "message": "Use worker start to recreate sandbox"}


@org_router.delete("/{agent_id}")
async def destroy_sandbox(org_id: str, agent_id: str):
    """Force-remove a sandbox container."""
    _validate_worker(org_id, agent_id)
    await sandbox_manager.destroy(org_id, agent_id)
    return {"status": "destroyed"}


def _validate_worker(org_id: str, agent_id: str) -> None:
    """Raise 404 if org or worker not found."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Org not found: {org_id}")
    agent = org.agent_registry.get(agent_id)
    if not agent or not getattr(agent, "is_external", False):
        raise HTTPException(404, f"Worker not found: {agent_id}")

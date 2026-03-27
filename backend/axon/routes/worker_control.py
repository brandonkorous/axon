"""Worker process control routes — start, stop, pause, resume, logs, status."""

from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException

import axon.registry as registry
from axon.runner_manager import runner_manager

logger = logging.getLogger(__name__)

org_router = APIRouter()

HEARTBEAT_TIMEOUT = 60  # seconds — runner is "connected" if polled within this


def _validate_worker(org_id: str, agent_id: str):
    """Raise 404 if org or worker not found."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Org not found: {org_id}")
    agent = org.agent_registry.get(agent_id)
    if not agent or not getattr(agent, "is_external", False):
        raise HTTPException(404, f"Worker not found: {agent_id}")


@org_router.post("/{agent_id}/start")
async def start_worker(org_id: str, agent_id: str):
    """Start the runner process for a worker agent."""
    _validate_worker(org_id, agent_id)
    try:
        await runner_manager.start(org_id, agent_id)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    return {"status": runner_manager.status(org_id, agent_id)}


@org_router.post("/{agent_id}/stop")
async def stop_worker(org_id: str, agent_id: str):
    """Stop the runner process for a worker agent."""
    _validate_worker(org_id, agent_id)
    await runner_manager.stop(org_id, agent_id)
    return {"status": "stopped"}


@org_router.post("/{agent_id}/pause")
async def pause_worker(org_id: str, agent_id: str):
    """Pause the runner process (stays alive, skips tasks)."""
    _validate_worker(org_id, agent_id)
    await runner_manager.pause(org_id, agent_id)
    return {"status": "paused"}


@org_router.post("/{agent_id}/resume")
async def resume_worker(org_id: str, agent_id: str):
    """Resume a paused runner process."""
    _validate_worker(org_id, agent_id)
    await runner_manager.resume(org_id, agent_id)
    return {"status": runner_manager.status(org_id, agent_id)}


@org_router.get("/{agent_id}/logs")
async def get_worker_logs(org_id: str, agent_id: str, lines: int = 100):
    """Return the last N lines of the runner log."""
    _validate_worker(org_id, agent_id)
    return {"lines": runner_manager.get_logs(org_id, agent_id, lines)}


@org_router.delete("/{agent_id}/logs")
async def clear_worker_logs(org_id: str, agent_id: str):
    """Clear the runner log file."""
    _validate_worker(org_id, agent_id)
    runner_manager.clear_logs(org_id, agent_id)
    return {"status": "cleared"}


@org_router.get("/{agent_id}/status")
async def worker_status(org_id: str, agent_id: str):
    """Get connection and process status for a worker agent."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Org not found: {org_id}")
    agent = org.agent_registry.get(agent_id)
    if not agent or not getattr(agent, "is_external", False):
        raise HTTPException(404, f"Worker not found: {agent_id}")

    last_poll = getattr(agent, "last_poll_time", None)
    connected = False
    last_seen = None
    if last_poll:
        elapsed = (datetime.utcnow() - last_poll).total_seconds()
        connected = elapsed < HEARTBEAT_TIMEOUT
        last_seen = last_poll.isoformat() + "Z"

    return {
        "agent_id": agent_id,
        "name": agent.name,
        "connected": connected,
        "last_seen": last_seen,
        "process_state": runner_manager.status(org_id, agent_id),
    }

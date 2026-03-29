"""Performance routes — agent effectiveness metrics and retrospectives."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

import axon.registry as registry
from axon.performance.tracker import PerformanceTracker

router = APIRouter()
org_router = APIRouter()


@org_router.get("/performance/{agent_id}")
async def get_agent_performance(org_id: str, agent_id: str, period: str = ""):
    """Get performance metrics for an agent."""
    org = registry.org_registry.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Org not found")
    if not org.shared_vault:
        raise HTTPException(status_code=404, detail="No shared vault")

    tracker = PerformanceTracker(org.shared_vault)
    metrics = tracker.get_metrics(agent_id, period)
    return metrics.model_dump()


@org_router.get("/performance/{agent_id}/history")
async def get_agent_performance_history(org_id: str, agent_id: str, limit: int = 12):
    """Get historical performance metrics for an agent."""
    org = registry.org_registry.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Org not found")
    if not org.shared_vault:
        raise HTTPException(status_code=404, detail="No shared vault")

    tracker = PerformanceTracker(org.shared_vault)
    metrics = tracker.get_all_metrics(agent_id, limit)
    return [m.model_dump() for m in metrics]


@org_router.get("/performance/{agent_id}/retro")
async def get_agent_retro(org_id: str, agent_id: str, period: str = ""):
    """Generate a retrospective analysis for an agent."""
    org = registry.org_registry.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Org not found")
    if not org.shared_vault:
        raise HTTPException(status_code=404, detail="No shared vault")

    agent = org.agent_registry.get(agent_id)
    agent_name = agent.name if agent else agent_id

    tracker = PerformanceTracker(org.shared_vault)
    retro = tracker.generate_retro(agent_id, agent_name, period)
    return retro.model_dump()

"""Pipeline routes -- CRUD and execution for agent pipelines."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import axon.registry as registry
from axon.pipelines.engine import PipelineEngine
from axon.pipelines.loader import get_pipeline, list_pipelines

router = APIRouter()
org_router = APIRouter()


class PipelineRunRequest(BaseModel):
    message: str


@org_router.get("")
async def list_org_pipelines(org_id: str):
    """List available pipelines for an org."""
    org = registry.org_registry.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Org not found")
    pipelines = list_pipelines(org_id)
    return [
        {
            "name": p.name,
            "description": p.description,
            "version": p.version,
            "steps": len(p.steps),
        }
        for p in pipelines
    ]


@org_router.post("/{pipeline_name}/run")
async def run_pipeline(
    org_id: str, pipeline_name: str, request: PipelineRunRequest,
):
    """Execute a pipeline and return results."""
    org = registry.org_registry.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Org not found")

    defn = get_pipeline(org_id, pipeline_name)
    if not defn:
        raise HTTPException(
            status_code=404,
            detail=f"Pipeline '{pipeline_name}' not found",
        )

    engine = PipelineEngine(org)
    events = []
    async for event in engine.run(defn, request.message):
        events.append({
            "type": event.type,
            "step_id": event.step_id,
            "agent_id": event.agent_id,
            "content": event.content,
            "metadata": event.metadata,
        })

    return {"pipeline": pipeline_name, "events": events}

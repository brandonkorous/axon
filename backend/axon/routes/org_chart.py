"""Org chart route — builds a node/edge graph from agent delegation config."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

import axon.registry as registry

router = APIRouter()
org_router = APIRouter()


def _build_org_chart(org_id: str):
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Organization not found: {org_id}")

    nodes = []
    edges = []

    for agent_id, agent in org.agent_registry.items():
        config = agent.config
        lifecycle = agent.lifecycle.to_dict() if hasattr(agent, "lifecycle") else {}

        nodes.append({
            "id": agent_id,
            "name": config.name,
            "title": config.title,
            "tagline": config.tagline,
            "color": config.ui.color,
            "status": lifecycle.get("status", "active"),
            "has_strategy_override": bool(lifecycle.get("strategy_override")),
        })

        # Build delegation edges
        delegates = config.delegation.can_delegate_to
        if delegates:
            for target in delegates:
                if target == "*":
                    # Wildcard: can delegate to all other agents
                    for other_id in org.agent_registry:
                        if other_id != agent_id:
                            edges.append({
                                "from": agent_id,
                                "to": other_id,
                                "type": "can_delegate_to",
                            })
                elif target in org.agent_registry:
                    edges.append({
                        "from": agent_id,
                        "to": target,
                        "type": "can_delegate_to",
                    })

        accepts = config.delegation.accepts_from
        if accepts:
            for source in accepts:
                if source == "*":
                    for other_id in org.agent_registry:
                        if other_id != agent_id:
                            # Only add if not already captured by can_delegate_to
                            edge = {"from": other_id, "to": agent_id, "type": "accepts_from"}
                            if edge not in edges:
                                edges.append(edge)
                elif source in org.agent_registry:
                    edge = {"from": source, "to": agent_id, "type": "accepts_from"}
                    if edge not in edges:
                        edges.append(edge)

    # Deduplicate edges
    seen = set()
    unique_edges = []
    for edge in edges:
        key = (edge["from"], edge["to"], edge["type"])
        if key not in seen:
            seen.add(key)
            unique_edges.append(edge)

    return {"nodes": nodes, "edges": unique_edges}


# ── Org-scoped routes ─────────────────────────────────────────────────


@org_router.get("")
async def get_org_chart_org(org_id: str):
    return _build_org_chart(org_id)


# ── Legacy routes ─────────────────────────────────────────────────────


@router.get("")
async def get_org_chart_legacy():
    return _build_org_chart(registry.default_org_id)

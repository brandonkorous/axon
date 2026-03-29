"""Analytics routes — comprehensive agent performance and system metrics."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select

import axon.registry as registry
from axon.db.agent_models import ConfidenceHistory, VaultEntry, VaultLink

router = APIRouter()
org_router = APIRouter()


async def _agent_metrics(agent, org) -> dict[str, Any]:
    """Build metrics for a single agent."""
    vault_path = Path(agent.config.vault.path)
    file_count = len(list(vault_path.rglob("*.md"))) if vault_path.exists() else 0

    confidence = {"current_avg": 0.0, "high": 0, "medium": 0, "low": 0, "total": 0, "history": []}
    memory = {"total_files": file_count, "active": 0, "archived": 0, "total_links": 0, "by_type": {}}

    if hasattr(agent, "_agent_db") and agent._agent_db is not None:
        async with agent._agent_db() as session:
            # Confidence distribution
            entries = (await session.execute(select(VaultEntry))).scalars().all()
            if entries:
                total_conf = 0.0
                for e in entries:
                    total_conf += e.confidence
                    if e.confidence >= 0.8:
                        confidence["high"] += 1
                    elif e.confidence >= 0.5:
                        confidence["medium"] += 1
                    else:
                        confidence["low"] += 1

                    if e.status == "active":
                        memory["active"] += 1
                    else:
                        memory["archived"] += 1

                    lt = e.learning_type or "other"
                    memory["by_type"][lt] = memory["by_type"].get(lt, 0) + 1

                confidence["total"] = len(entries)
                confidence["current_avg"] = round(total_conf / len(entries), 3)

            # Link density
            link_count = (await session.execute(select(func.count()).select_from(VaultLink))).scalar() or 0
            memory["total_links"] = link_count

            # Confidence history (last 30 data points, grouped by date)
            rows = (await session.execute(
                select(ConfidenceHistory.date, func.avg(ConfidenceHistory.value))
                .group_by(ConfidenceHistory.date)
                .order_by(ConfidenceHistory.date.desc())
                .limit(30)
            )).all()
            confidence["history"] = [
                {"date": r[0], "avg": round(r[1], 3)} for r in reversed(rows)
            ]

    # Usage stats for this agent
    usage = {"cost": 0.0, "tokens": 0, "requests": 0}
    if org.usage_tracker:
        for rec in org.usage_tracker._iter_records():
            if rec.get("agent_id") == agent.id:
                usage["cost"] += rec.get("cost", 0.0)
                usage["tokens"] += rec.get("total_tokens", 0)
                usage["requests"] += 1

    usage["cost"] = round(usage["cost"], 6)

    return {
        "id": agent.id,
        "name": agent.name,
        "title": agent.config.title,
        "color": agent.config.ui.color,
        "status": agent.lifecycle.status.value if hasattr(agent, "lifecycle") else "idle",
        "model": agent.config.model if hasattr(agent.config, "model") else "",
        "confidence": confidence,
        "memory": memory,
        "usage": usage,
        "message_count": len(agent.conversation.messages),
    }


def _build_activity_timeline(org, days: int = 30) -> list[dict[str, Any]]:
    """Build daily activity counts from audit log."""
    if not org.audit_logger:
        return []

    daily: dict[str, dict[str, Any]] = defaultdict(lambda: {"actions": 0, "agents": set()})
    entries = org.audit_logger.list_entries(limit=5000)

    for entry in entries:
        ts = entry.get("timestamp", "")
        day = ts[:10] if len(ts) >= 10 else ""
        if not day:
            continue
        daily[day]["actions"] += 1
        daily[day]["agents"].add(entry.get("agent_id", ""))

    result = []
    for day in sorted(daily.keys(), reverse=True)[:days]:
        result.append({
            "date": day,
            "actions": daily[day]["actions"],
            "unique_agents": len(daily[day]["agents"]),
        })
    return list(reversed(result))


def _build_tool_usage(org) -> dict[str, int]:
    """Aggregate tool usage counts from audit log."""
    if not org.audit_logger:
        return {}

    counts: dict[str, int] = defaultdict(int)
    entries = org.audit_logger.list_entries(limit=5000)
    for entry in entries:
        tool = entry.get("tool", "") or entry.get("action", "")
        if tool:
            counts[tool] += 1

    return dict(sorted(counts.items(), key=lambda x: -x[1]))


def _build_delegation_flow(org) -> list[dict[str, Any]]:
    """Extract delegation patterns from audit log."""
    if not org.audit_logger:
        return []

    flows: dict[str, int] = defaultdict(int)
    entries = org.audit_logger.list_entries(limit=5000, action="delegation")
    for entry in entries:
        src = entry.get("agent_id", "unknown")
        target = entry.get("tool", "unknown")  # delegation target stored in tool field
        key = f"{src}→{target}"
        flows[key] += 1

    return [
        {"from": k.split("→")[0], "to": k.split("→")[1], "count": v}
        for k, v in sorted(flows.items(), key=lambda x: -x[1])
    ]


def _get_task_metrics(org_id: str) -> dict[str, Any]:
    """Task completion metrics."""
    from axon.routes.tasks import _parse_tasks

    org = registry.get_org(org_id)
    if not org or not org.shared_vault:
        return {"total": 0, "completed": 0, "in_progress": 0, "pending": 0, "completion_rate": 0}

    tasks = _parse_tasks(org.shared_vault)
    counts: dict[str, int] = defaultdict(int)
    by_agent: dict[str, dict[str, int]] = defaultdict(lambda: {"completed": 0, "total": 0})

    for t in tasks:
        status = t.get("status", "pending")
        counts[status] += 1
        assignee = t.get("assignee", "unassigned")
        by_agent[assignee]["total"] += 1
        if status in ("completed", "done"):
            by_agent[assignee]["completed"] += 1

    total = len(tasks)
    completed = counts.get("completed", 0) + counts.get("done", 0)

    return {
        "total": total,
        "completed": completed,
        "in_progress": counts.get("in_progress", 0),
        "pending": counts.get("pending", 0),
        "completion_rate": round(completed / total * 100, 1) if total > 0 else 0,
        "by_agent": dict(by_agent),
    }


async def _build_analytics(org_id: str) -> dict[str, Any]:
    """Build the full analytics response."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Organization not found: {org_id}")

    # Per-agent metrics
    agent_metrics = []
    for agent in org.agent_registry.values():
        metrics = await _agent_metrics(agent, org)
        agent_metrics.append(metrics)

    # System totals
    total_cost = sum(a["usage"]["cost"] for a in agent_metrics)
    total_tokens = sum(a["usage"]["tokens"] for a in agent_metrics)
    total_requests = sum(a["usage"]["requests"] for a in agent_metrics)
    total_files = sum(a["memory"]["total_files"] for a in agent_metrics)
    total_links = sum(a["memory"]["total_links"] for a in agent_metrics)
    avg_confidence = (
        sum(a["confidence"]["current_avg"] for a in agent_metrics) / len(agent_metrics)
        if agent_metrics else 0
    )

    tasks = _get_task_metrics(org_id)

    return {
        "agents": agent_metrics,
        "totals": {
            "total_agents": len(agent_metrics),
            "total_cost": round(total_cost, 6),
            "total_tokens": total_tokens,
            "total_requests": total_requests,
            "total_vault_files": total_files,
            "total_links": total_links,
            "avg_confidence": round(avg_confidence, 3),
        },
        "tasks": tasks,
        "activity_timeline": _build_activity_timeline(org),
        "tool_usage": _build_tool_usage(org),
        "delegation_flow": _build_delegation_flow(org),
    }


# ── Org-scoped routes ────────────────────────────────────────────────


@org_router.get("")
async def get_analytics(org_id: str):
    """Get comprehensive analytics for an organization."""
    return await _build_analytics(org_id)


# ── Legacy routes ────────────────────────────────────────────────────


@router.get("")
async def get_analytics_legacy():
    """Get analytics for the default organization."""
    return await _build_analytics(registry.default_org_id)

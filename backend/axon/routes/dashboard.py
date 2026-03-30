"""Dashboard routes — aggregated data for the command center overview."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

import axon.registry as registry
from axon.vault.frontmatter import parse_frontmatter

router = APIRouter()
org_router = APIRouter()


def _get_agent_summaries(agent_reg: dict) -> list[dict[str, Any]]:
    """Get summary info for all agents."""
    summaries = []
    for agent_id, agent in agent_reg.items():
        vault_path = Path(agent.config.vault.path)
        file_count = len(list(vault_path.rglob("*.md"))) if vault_path.exists() else 0

        summaries.append({
            "id": agent.id,
            "name": agent.name,
            "title": agent.config.title,
            "color": agent.config.ui.color,
            "avatar": agent.config.ui.avatar,
            "status": agent.lifecycle.status.value if hasattr(agent, "lifecycle") else "idle",
            "vault_files": file_count,
            "message_count": len(agent.conversation.messages),
        })
    return summaries


def _scan_vault_decisions(vaults_dir: Path, limit: int = 10) -> list[dict[str, Any]]:
    """Scan vault directories for decision files."""
    decisions: list[dict[str, Any]] = []
    if not vaults_dir.exists():
        return []

    for vault_dir in vaults_dir.iterdir():
        if not vault_dir.is_dir():
            continue
        decisions_dir = vault_dir / "decisions"
        if not decisions_dir.exists():
            continue

        for md_file in decisions_dir.glob("*.md"):
            if md_file.name.endswith("-index.md") or md_file.name.endswith("-log.md"):
                continue
            try:
                content = md_file.read_text(encoding="utf-8")
                metadata, _ = parse_frontmatter(content)
                decisions.append({
                    "vault": vault_dir.name,
                    "path": str(md_file.relative_to(vault_dir)),
                    "name": metadata.get("name", md_file.stem),
                    "description": metadata.get("description", ""),
                    "date": metadata.get("date", ""),
                    "status": metadata.get("status", ""),
                })
            except Exception:
                continue

    decisions.sort(key=lambda d: str(d.get("date", "")), reverse=True)
    return decisions[:limit]


def _scan_vault_pending_actions(vaults_dir: Path) -> list[dict[str, Any]]:
    """Find pending action items and inbox tasks across vault directories."""
    actions: list[dict[str, Any]] = []
    if not vaults_dir.exists():
        return []

    for vault_dir in vaults_dir.iterdir():
        if not vault_dir.is_dir():
            continue

        # Check inbox
        inbox_dir = vault_dir / "inbox"
        if inbox_dir.exists():
            for md_file in inbox_dir.glob("*.md"):
                if md_file.name == "README.md":
                    continue
                try:
                    content = md_file.read_text(encoding="utf-8")
                    metadata, _ = parse_frontmatter(content)
                    if metadata.get("status") == "pending":
                        actions.append({
                            "vault": vault_dir.name,
                            "path": str(md_file.relative_to(vault_dir)),
                            "type": "inbox_task",
                            "from": metadata.get("from", ""),
                            "priority": metadata.get("priority", "medium"),
                            "date": metadata.get("date", ""),
                        })
                except Exception:
                    continue

        # Check action-items
        actions_dir = vault_dir / "action-items"
        if actions_dir.exists():
            for md_file in actions_dir.glob("*.md"):
                if md_file.name.endswith("-index.md"):
                    continue
                try:
                    content = md_file.read_text(encoding="utf-8")
                    metadata, _ = parse_frontmatter(content)
                    if metadata.get("status") in ("active", "pending"):
                        actions.append({
                            "vault": vault_dir.name,
                            "path": str(md_file.relative_to(vault_dir)),
                            "type": "action_item",
                            "name": metadata.get("name", md_file.stem),
                            "date": metadata.get("date", ""),
                        })
                except Exception:
                    continue

    return actions


# ── Widget data helpers ──────────────────────────────────────────────


def _get_task_summary(org_id: str) -> dict[str, Any]:
    """Get task counts by status and recent tasks."""
    from axon.routes.tasks import _parse_tasks

    org = registry.get_org(org_id)
    if not org or not org.shared_vault:
        return {"counts": {}, "recent": []}

    tasks = _parse_tasks(org.shared_vault)
    counts: dict[str, int] = {}
    for t in tasks:
        s = t.get("status", "pending")
        counts[s] = counts.get(s, 0) + 1

    recent = tasks[:5]
    return {
        "counts": counts,
        "total": len(tasks),
        "recent": [
            {
                "path": t.get("path", ""),
                "name": t.get("name", ""),
                "status": t.get("status", ""),
                "priority": t.get("priority", ""),
                "assignee": t.get("assignee", ""),
            }
            for t in recent
        ],
    }


def _get_issue_summary(org_id: str) -> dict[str, Any]:
    """Get issue counts by status and recent issues."""
    org = registry.get_org(org_id)
    if not org or not org.shared_vault:
        return {"counts": {}, "recent": []}

    vault = org.shared_vault
    issues_dir = Path(vault.vault_path) / "issues"
    if not issues_dir.exists():
        return {"counts": {}, "total": 0, "recent": []}

    issues = []
    for md_file in sorted(issues_dir.glob("*.md"), reverse=True):
        if md_file.name.endswith("-index.md"):
            continue
        try:
            metadata, _ = vault.read_file(f"issues/{md_file.name}")
            metadata["path"] = f"issues/{md_file.name}"
            issues.append(metadata)
        except Exception:
            continue

    counts: dict[str, int] = {}
    for issue in issues:
        s = issue.get("status", "open")
        counts[s] = counts.get(s, 0) + 1

    return {
        "counts": counts,
        "total": len(issues),
        "recent": [
            {
                "path": i.get("path", ""),
                "name": i.get("name", ""),
                "id": i.get("id", ""),
                "status": i.get("status", ""),
                "priority": i.get("priority", ""),
                "assignee": i.get("assignee", ""),
            }
            for i in issues[:5]
        ],
    }


def _get_audit_summary(org_id: str) -> dict[str, Any]:
    """Get recent audit entries and total count."""
    org = registry.get_org(org_id)
    if not org or not org.audit_logger:
        return {"total": 0, "recent": []}

    total = org.audit_logger.count_entries()
    recent = org.audit_logger.list_entries(limit=8)

    return {
        "total": total,
        "recent": [
            {
                "timestamp": e.get("timestamp", ""),
                "agent_id": e.get("agent_id", ""),
                "action": e.get("action", ""),
                "tool": e.get("tool", ""),
            }
            for e in recent
        ],
    }


def _get_achievement_summary(org_id: str) -> list[dict[str, Any]]:
    """Get recent achievements."""
    org = registry.get_org(org_id)
    if not org or not org.shared_vault:
        return []

    vault = org.shared_vault
    achievements_dir = Path(vault.vault_path) / "achievements"
    if not achievements_dir.exists():
        return []

    achievements = []
    for md_file in sorted(achievements_dir.glob("*.md"), reverse=True):
        if md_file.name.endswith("-index.md"):
            continue
        try:
            metadata, _ = vault.read_file(f"achievements/{md_file.name}")
            achievements.append({
                "name": metadata.get("name", ""),
                "impact": metadata.get("impact", ""),
                "date": metadata.get("date", ""),
                "agents_involved": metadata.get("agents_involved", []),
            })
        except Exception:
            continue

    return achievements[:5]


# ── Build response ───────────────────────────────────────────────────


def _build_dashboard(
    agent_reg: dict,
    vaults_dir: Path | None = None,
    org_id: str = "default",
) -> dict:
    """Build the full dashboard response."""
    result: dict[str, Any] = {
        "agents": _get_agent_summaries(agent_reg),
        "recent_decisions": [],
        "pending_actions": [],
        "tasks": _get_task_summary(org_id),
        "issues": _get_issue_summary(org_id),
        "audit": _get_audit_summary(org_id),
        "achievements": _get_achievement_summary(org_id),
    }
    if vaults_dir:
        result["recent_decisions"] = _scan_vault_decisions(vaults_dir, limit=10)
        result["pending_actions"] = _scan_vault_pending_actions(vaults_dir)
    return result


# ── Legacy routes (default org) ─────────────────────────────────────


@router.get("")
async def get_dashboard():
    """Get dashboard data: agent status, recent decisions, pending actions."""
    org = registry.get_default_org()
    vaults_dir = None
    if org:
        for agent in org.agent_registry.values():
            vault_path = Path(agent.config.vault.path)
            if vault_path.exists():
                vaults_dir = vault_path.parent
                break
    return await asyncio.to_thread(
        _build_dashboard, registry.agent_registry, vaults_dir, registry.default_org_id,
    )


# ── Org-scoped routes ───────────────────────────────────────────────


@org_router.get("")
async def get_org_dashboard(org_id: str):
    """Get dashboard data for an organization."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization not found: {org_id}")

    vaults_dir = None
    for agent in org.agent_registry.values():
        vault_path = Path(agent.config.vault.path)
        if vault_path.exists():
            vaults_dir = vault_path.parent
            break

    return await asyncio.to_thread(
        _build_dashboard, org.agent_registry, vaults_dir, org_id,
    )

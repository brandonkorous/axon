"""Dashboard routes — aggregated data for the command center overview."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter

from axon.config import settings
from axon.registry import agent_registry
from axon.vault.frontmatter import parse_frontmatter

router = APIRouter()


@router.get("")
async def get_dashboard():
    """Get dashboard data: agent status, recent decisions, pending actions."""
    return {
        "agents": _get_agent_summaries(),
        "recent_decisions": _get_recent_decisions(limit=10),
        "pending_actions": _get_pending_actions(),
    }


def _get_agent_summaries() -> list[dict[str, Any]]:
    """Get summary info for all agents."""
    summaries = []
    for agent_id, agent in agent_registry.items():
        vault_path = Path(agent.config.vault.path)
        file_count = len(list(vault_path.rglob("*.md"))) if vault_path.exists() else 0

        summaries.append({
            "id": agent.id,
            "name": agent.name,
            "title": agent.config.title,
            "color": agent.config.ui.color,
            "avatar": agent.config.ui.avatar,
            "status": "idle",
            "vault_files": file_count,
            "message_count": len(agent.conversation.messages),
        })
    return summaries


def _get_recent_decisions(limit: int = 10) -> list[dict[str, Any]]:
    """Aggregate recent decisions from all agent vaults."""
    decisions: list[dict[str, Any]] = []
    vaults_dir = Path(settings.axon_vaults_dir)

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

    # Sort by date descending
    decisions.sort(key=lambda d: d.get("date", ""), reverse=True)
    return decisions[:limit]


def _get_pending_actions() -> list[dict[str, Any]]:
    """Find pending action items and inbox tasks across all vaults."""
    actions: list[dict[str, Any]] = []
    vaults_dir = Path(settings.axon_vaults_dir)

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

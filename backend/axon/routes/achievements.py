"""Achievement routes — list and view milestones."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import axon.registry as registry

router = APIRouter()
org_router = APIRouter()


class AchievementCreate(BaseModel):
    title: str
    description: str = ""
    impact: str = ""
    agents_involved: list[str] = []
    linked_tasks: list[str] = []
    linked_issues: list[str] = []


def _get_shared_vault(org_id: str):
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Organization not found: {org_id}")
    if not org.shared_vault:
        raise HTTPException(404, f"No shared vault for org: {org_id}")
    return org.shared_vault


def _list_achievements(org_id: str) -> list[dict[str, Any]]:
    vault = _get_shared_vault(org_id)
    achievements_dir = Path(vault.vault_path) / "achievements"
    if not achievements_dir.exists():
        return []

    achievements = []
    for md_file in sorted(achievements_dir.glob("*.md"), reverse=True):
        if md_file.name.endswith("-index.md"):
            continue
        try:
            metadata, body = vault.read_file(f"achievements/{md_file.name}")
            achievements.append({**metadata, "path": f"achievements/{md_file.name}", "body": body})
        except Exception:
            continue
    return achievements


def _create_achievement(org_id: str, data: AchievementCreate):
    from axon.agents.shared_tools import _slugify

    vault = _get_shared_vault(org_id)
    slug = _slugify(data.title)
    today_str = str(datetime.utcnow().date())
    path = f"achievements/{today_str}-{slug}.md"

    metadata = {
        "name": data.title,
        "type": "achievement",
        "agents_involved": data.agents_involved,
        "linked_tasks": data.linked_tasks,
        "linked_issues": data.linked_issues,
        "impact": data.impact,
        "date": today_str,
        "created_by": "user",
        "created_at": datetime.utcnow().isoformat() + "Z",
    }

    content = f"# {data.title}\n\n{data.description}"
    if data.impact:
        content += f"\n\n## Impact\n{data.impact}"

    vault.write_file(path, metadata, content)
    vault._update_branch_index("achievements", slug, data.title)

    return {**metadata, "path": path, "body": content}


# ── Org-scoped routes ─────────────────────────────────────────────────


@org_router.get("")
async def list_achievements_org(org_id: str):
    return _list_achievements(org_id)


@org_router.post("")
async def create_achievement_org(org_id: str, data: AchievementCreate):
    return _create_achievement(org_id, data)


# ── Legacy routes ─────────────────────────────────────────────────────


@router.get("")
async def list_achievements_legacy():
    return _list_achievements(registry.default_org_id)


@router.post("")
async def create_achievement_legacy(data: AchievementCreate):
    return _create_achievement(registry.default_org_id, data)

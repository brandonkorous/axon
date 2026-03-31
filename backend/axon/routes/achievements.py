"""Achievement routes — read-only list and view milestones.

Achievements are auto-generated when a parent task reaches 'accepted' status.
Manual creation is not supported via the API.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

import axon.registry as registry

router = APIRouter()
org_router = APIRouter()


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


# ── Org-scoped routes ─────────────────────────────────────────────────


@org_router.get("")
async def list_achievements_org(org_id: str):
    return _list_achievements(org_id)


# ── Legacy routes ─────────────────────────────────────────────────────


@router.get("")
async def list_achievements_legacy():
    return _list_achievements(registry.default_org_id)

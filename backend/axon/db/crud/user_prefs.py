"""CRUD operations for user preferences in central axon.db."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from axon.db.models import UserPreference

DEFAULT_USER_ID = "default"


async def get_prefs(
    session: AsyncSession,
    user_id: str = DEFAULT_USER_ID,
) -> dict[str, Any]:
    """Get user preferences. Returns defaults if no row exists."""
    result = await session.execute(
        select(UserPreference).where(UserPreference.user_id == user_id)
    )
    row = result.scalar_one_or_none()
    if not row:
        return {
            "user_id": user_id,
            "theme": "dark",
            "voice_settings": {},
            "display_prefs": {},
        }
    return {
        "user_id": row.user_id,
        "theme": row.theme,
        "voice_settings": json.loads(row.voice_settings_json),
        "display_prefs": json.loads(row.display_prefs_json),
    }


async def update_prefs(
    session: AsyncSession,
    patch: dict[str, Any],
    user_id: str = DEFAULT_USER_ID,
) -> dict[str, Any]:
    """Upsert user preferences. Returns the updated prefs dict."""
    result = await session.execute(
        select(UserPreference).where(UserPreference.user_id == user_id)
    )
    row = result.scalar_one_or_none()

    if not row:
        row = UserPreference(user_id=user_id)
        session.add(row)

    if "theme" in patch:
        row.theme = patch["theme"]
    if "voice_settings" in patch:
        row.voice_settings_json = json.dumps(patch["voice_settings"])
    if "display_prefs" in patch:
        row.display_prefs_json = json.dumps(patch["display_prefs"])

    await session.commit()
    await session.refresh(row)

    return {
        "user_id": row.user_id,
        "theme": row.theme,
        "voice_settings": json.loads(row.voice_settings_json),
        "display_prefs": json.loads(row.display_prefs_json),
    }

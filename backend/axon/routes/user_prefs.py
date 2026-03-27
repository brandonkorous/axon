"""User preferences routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from axon.db.engine import get_session
from axon.db.crud import user_prefs as prefs_crud

router = APIRouter()


class UpdatePrefsRequest(BaseModel):
    """Updatable preference fields."""

    theme: str | None = None
    voice_settings: dict | None = None
    display_prefs: dict | None = None


@router.get("")
async def get_preferences(session: AsyncSession = Depends(get_session)):
    """Get the current user's preferences."""
    return await prefs_crud.get_prefs(session)


@router.patch("")
async def update_preferences(
    body: UpdatePrefsRequest,
    session: AsyncSession = Depends(get_session),
):
    """Update the current user's preferences."""
    patch = body.model_dump(exclude_none=True)
    return await prefs_crud.update_prefs(session, patch)

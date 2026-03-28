"""Push notification routes — subscription management and VAPID key endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from axon.db.crud.push import (
    delete_subscription,
    get_or_create_vapid_keys,
    save_subscription,
)
from axon.db.engine import get_session

router = APIRouter()


class SubscribeRequest(BaseModel):
    endpoint: str
    keys: dict[str, str]  # {"p256dh": "...", "auth": "..."}


class UnsubscribeRequest(BaseModel):
    endpoint: str


@router.get("/vapid-public-key")
async def vapid_public_key(session: AsyncSession = Depends(get_session)):
    """Return the VAPID public key for push subscription."""
    public_key, _ = await get_or_create_vapid_keys(session)
    return {"public_key": public_key}


@router.post("/subscribe")
async def subscribe(
    body: SubscribeRequest,
    session: AsyncSession = Depends(get_session),
):
    """Register a browser push subscription."""
    sub = await save_subscription(
        session,
        endpoint=body.endpoint,
        p256dh=body.keys["p256dh"],
        auth=body.keys["auth"],
    )
    return {"ok": True, "id": sub.id}


@router.delete("/subscribe")
async def unsubscribe(
    body: UnsubscribeRequest,
    session: AsyncSession = Depends(get_session),
):
    """Remove a browser push subscription."""
    removed = await delete_subscription(session, body.endpoint)
    return {"ok": removed}

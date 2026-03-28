"""CRUD operations for Web Push subscriptions and VAPID keys."""

from __future__ import annotations

import base64
import uuid

from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from py_vapid import Vapid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from axon.db.encryption import decrypt_token, encrypt_token
from axon.db.models import PushSubscription, VapidKeys


async def get_or_create_vapid_keys(session: AsyncSession) -> tuple[str, str]:
    """Return (public_key_urlsafe_b64, private_key_pem). Generates on first call."""
    result = await session.execute(
        select(VapidKeys).where(VapidKeys.id == "default")
    )
    row = result.scalar_one_or_none()
    if row:
        return row.public_key, decrypt_token(row.private_key_enc)

    # Generate fresh VAPID key pair
    vapid = Vapid()
    vapid.generate_keys()
    raw_private = vapid.private_pem().decode()
    # Encode public key as uncompressed point in URL-safe base64 (no padding)
    pub_bytes = vapid.public_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
    raw_public = base64.urlsafe_b64encode(pub_bytes).decode().rstrip("=")

    row = VapidKeys(
        id="default",
        public_key=raw_public,
        private_key_enc=encrypt_token(raw_private),
    )
    session.add(row)
    await session.commit()
    return raw_public, raw_private


async def save_subscription(
    session: AsyncSession,
    *,
    endpoint: str,
    p256dh: str,
    auth: str,
    user_id: str = "default",
) -> PushSubscription:
    """Upsert a push subscription by endpoint."""
    result = await session.execute(
        select(PushSubscription).where(PushSubscription.endpoint == endpoint)
    )
    row = result.scalar_one_or_none()
    if row:
        row.p256dh = p256dh
        row.auth = auth
        row.user_id = user_id
    else:
        row = PushSubscription(
            id=str(uuid.uuid4()),
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
            user_id=user_id,
        )
        session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def delete_subscription(session: AsyncSession, endpoint: str) -> bool:
    """Remove a push subscription by endpoint."""
    result = await session.execute(
        select(PushSubscription).where(PushSubscription.endpoint == endpoint)
    )
    row = result.scalar_one_or_none()
    if not row:
        return False
    await session.delete(row)
    await session.commit()
    return True


async def get_all_subscriptions(session: AsyncSession) -> list[PushSubscription]:
    """Return all active push subscriptions."""
    result = await session.execute(select(PushSubscription))
    return list(result.scalars().all())

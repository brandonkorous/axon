"""CRUD operations for organization settings in central axon.db."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from axon.db.models import OrgSettings


async def get_settings(session: AsyncSession, org_id: str) -> dict[str, Any] | None:
    """Get org settings by org_id."""
    result = await session.execute(
        select(OrgSettings).where(OrgSettings.org_id == org_id)
    )
    row = result.scalar_one_or_none()
    if not row:
        return None
    return {
        "org_id": row.org_id,
        "name": row.name,
        "description": row.description,
        "type": row.type,
        "comms": {
            "require_approval": row.comms_require_approval,
            "email_domain": row.comms_email_domain,
            "email_signature": row.comms_email_signature,
            "inbound_polling": row.comms_inbound_polling,
        },
    }


async def update_settings(
    session: AsyncSession,
    org_id: str,
    patch: dict[str, Any],
) -> dict[str, Any]:
    """Upsert org settings. Returns the updated settings dict."""
    result = await session.execute(
        select(OrgSettings).where(OrgSettings.org_id == org_id)
    )
    row = result.scalar_one_or_none()

    if not row:
        row = OrgSettings(org_id=org_id)
        session.add(row)

    if "name" in patch:
        row.name = patch["name"]
    if "description" in patch:
        row.description = patch["description"]
    if "type" in patch:
        row.type = patch["type"]

    comms = patch.get("comms")
    if comms:
        if "require_approval" in comms:
            row.comms_require_approval = comms["require_approval"]
        if "email_domain" in comms:
            row.comms_email_domain = comms["email_domain"]
        if "email_signature" in comms:
            row.comms_email_signature = comms["email_signature"]
        if "inbound_polling" in comms:
            row.comms_inbound_polling = comms["inbound_polling"]

    await session.commit()
    await session.refresh(row)

    return {
        "org_id": row.org_id,
        "name": row.name,
        "description": row.description,
        "type": row.type,
        "comms": {
            "require_approval": row.comms_require_approval,
            "email_domain": row.comms_email_domain,
            "email_signature": row.comms_email_signature,
            "inbound_polling": row.comms_inbound_polling,
        },
    }


async def seed_from_config(
    session: AsyncSession,
    org_id: str,
    name: str,
    description: str,
    org_type: str,
    comms: dict[str, Any],
) -> None:
    """Seed org settings from org.yaml on first run (no-op if row exists)."""
    result = await session.execute(
        select(OrgSettings).where(OrgSettings.org_id == org_id)
    )
    if result.scalar_one_or_none():
        return  # Already seeded

    session.add(OrgSettings(
        org_id=org_id,
        name=name,
        description=description,
        type=org_type,
        comms_require_approval=comms.get("require_approval", True),
        comms_email_domain=comms.get("email_domain", ""),
        comms_email_signature=comms.get("email_signature", ""),
        comms_inbound_polling=comms.get("inbound_polling", False),
    ))
    await session.commit()

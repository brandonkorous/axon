"""Credential management routes — encrypted per-org API keys."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from axon.db.engine import get_session
from axon.db.crud.credentials import (
    create_credential,
    delete_credential,
    get_access_token,
    get_org_credentials,
    update_tokens,
)
import axon.registry as registry

logger = logging.getLogger(__name__)

org_router = APIRouter()

VALID_PROVIDERS = {"resend", "discord"}


class CreateCredentialRequest(BaseModel):
    provider: str
    access_token: str
    label: str = ""


def _mask_token(token: str) -> str:
    """Show only the last 4 characters of a token."""
    if len(token) <= 4:
        return "****"
    return "*" * (len(token) - 4) + token[-4:]


@org_router.get("")
async def list_credentials(
    org_id: str,
    session: AsyncSession = Depends(get_session),
):
    """List credentials for an org (tokens are masked)."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Organization not found: {org_id}")

    creds = await get_org_credentials(session, org_id)
    return [
        {
            "id": c.id,
            "provider": c.provider,
            "label": c.label,
            "token_preview": _mask_token(get_access_token(c)),
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in creds
    ]


@org_router.post("")
async def add_credential(
    org_id: str,
    body: CreateCredentialRequest,
    session: AsyncSession = Depends(get_session),
):
    """Create or update a credential for an org.

    One credential per provider per org — upserts if existing.
    """
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Organization not found: {org_id}")
    if body.provider not in VALID_PROVIDERS:
        raise HTTPException(400, f"Invalid provider. Must be one of: {', '.join(sorted(VALID_PROVIDERS))}")
    if not body.access_token.strip():
        raise HTTPException(400, "access_token is required")

    # Upsert: update existing credential or create new one
    existing = await get_org_credentials(session, org_id, provider=body.provider)
    if existing:
        cred = await update_tokens(session, existing[0].id, access_token=body.access_token)
        logger.info("Updated %s credential for org %s", body.provider, org_id)
    else:
        cred = await create_credential(
            session,
            org_id=org_id,
            provider=body.provider,
            access_token=body.access_token,
            label=body.label or body.provider.title(),
        )
        logger.info("Created %s credential for org %s", body.provider, org_id)

    return {
        "id": cred.id,
        "provider": cred.provider,
        "label": cred.label,
        "created_at": cred.created_at.isoformat() if cred.created_at else None,
    }


@org_router.delete("/{credential_id}")
async def remove_credential(
    org_id: str,
    credential_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Delete a credential."""
    from axon.db.crud.credentials import get_credential

    cred = await get_credential(session, credential_id)
    if not cred or cred.org_id != org_id:
        raise HTTPException(404, "Credential not found")

    await delete_credential(session, credential_id)
    logger.info("Deleted credential %s for org %s", credential_id, org_id)
    return {"status": "deleted"}

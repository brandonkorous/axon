"""CRUD operations for credentials and connected accounts."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from axon.db.encryption import decrypt_token, encrypt_token
from axon.db.models import ConnectedAccount, Credential


async def create_credential(
    session: AsyncSession,
    *,
    org_id: str,
    provider: str,
    access_token: str,
    refresh_token: str | None = None,
    token_expiry: datetime | None = None,
    label: str = "",
    scopes: str = "",
    metadata_json: str = "{}",
) -> Credential:
    """Create an encrypted credential record."""
    cred = Credential(
        id=str(uuid.uuid4()),
        org_id=org_id,
        provider=provider,
        label=label,
        access_token_enc=encrypt_token(access_token),
        refresh_token_enc=encrypt_token(refresh_token) if refresh_token else None,
        token_expiry=token_expiry,
        scopes=scopes,
        metadata_json=metadata_json,
    )
    session.add(cred)
    await session.commit()
    await session.refresh(cred)
    return cred


async def get_credential(session: AsyncSession, credential_id: str) -> Credential | None:
    """Fetch a credential by ID."""
    return await session.get(Credential, credential_id)


async def get_org_credentials(
    session: AsyncSession,
    org_id: str,
    provider: str | None = None,
) -> list[Credential]:
    """List credentials for an org, optionally filtered by provider."""
    stmt = select(Credential).where(Credential.org_id == org_id)
    if provider:
        stmt = stmt.where(Credential.provider == provider)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_tokens(
    session: AsyncSession,
    credential_id: str,
    *,
    access_token: str,
    refresh_token: str | None = None,
    token_expiry: datetime | None = None,
) -> Credential | None:
    """Update tokens after an OAuth refresh."""
    cred = await session.get(Credential, credential_id)
    if not cred:
        return None
    cred.access_token_enc = encrypt_token(access_token)
    if refresh_token is not None:
        cred.refresh_token_enc = encrypt_token(refresh_token)
    if token_expiry is not None:
        cred.token_expiry = token_expiry
    await session.commit()
    await session.refresh(cred)
    return cred


async def delete_credential(session: AsyncSession, credential_id: str) -> bool:
    """Delete a credential and its connected accounts (cascade)."""
    cred = await session.get(Credential, credential_id)
    if not cred:
        return False
    await session.delete(cred)
    await session.commit()
    return True


def get_access_token(cred: Credential) -> str:
    """Decrypt the access token from a credential record."""
    return decrypt_token(cred.access_token_enc)


def get_refresh_token(cred: Credential) -> str | None:
    """Decrypt the refresh token from a credential record."""
    if not cred.refresh_token_enc:
        return None
    return decrypt_token(cred.refresh_token_enc)


async def link_account(
    session: AsyncSession,
    *,
    user_id: str,
    credential_id: str,
    provider: str,
    provider_account_id: str,
) -> ConnectedAccount:
    """Link a user to a credential via a connected account."""
    account = ConnectedAccount(
        id=str(uuid.uuid4()),
        user_id=user_id,
        credential_id=credential_id,
        provider=provider,
        provider_account_id=provider_account_id,
    )
    session.add(account)
    await session.commit()
    await session.refresh(account)
    return account

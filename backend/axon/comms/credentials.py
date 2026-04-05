"""Credential resolution — look up encrypted API keys from the DB per org."""

from __future__ import annotations

from axon.logging import get_logger

logger = get_logger(__name__)


async def resolve_credential(org_id: str, provider: str) -> str | None:
    """Resolve a decrypted API key for *provider* in *org_id*.

    Returns the plaintext token or None if no credential exists.
    """
    from axon.db.engine import get_session
    from axon.db.crud.credentials import get_org_credentials, get_access_token

    try:
        async for session in get_session():
            creds = await get_org_credentials(session, org_id, provider=provider)
            if creds:
                return get_access_token(creds[0])
    except Exception:
        logger.exception("Failed to resolve %s credential for org %s", provider, org_id)
    return None

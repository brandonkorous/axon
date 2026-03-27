"""Credential bridge — load credentials from the DB for integrations."""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


async def load_integration_credentials(
    org_id: str,
    integration_names: list[str],
) -> dict[str, dict[str, Any]]:
    """Load credentials for integrations from the credential store.

    Matches integration names to credential providers. Returns a map
    of {integration_name: {access_token, api_key, ...}} for each
    integration that has a stored credential.
    """
    if not org_id or not integration_names:
        return {}

    from axon.db.engine import _session_factory
    from axon.db.crud.credentials import get_org_credentials, get_access_token

    credentials_map: dict[str, dict[str, Any]] = {}

    if _session_factory is None:
        logger.debug("Database not initialized yet — skipping credential load")
        return credentials_map

    try:
        async with _session_factory() as session:
            for name in integration_names:
                # Provider name in the credential store may match the
                # integration name directly or use a known alias
                provider = _integration_to_provider(name)
                creds = await get_org_credentials(session, org_id, provider=provider)
                if creds:
                    cred = creds[0]
                    token = get_access_token(cred)
                    metadata = {}
                    if cred.metadata_json:
                        try:
                            metadata = json.loads(cred.metadata_json)
                        except json.JSONDecodeError:
                            pass
                    credentials_map[name] = {
                        "access_token": token,
                        "api_key": token,
                        "scopes": cred.scopes,
                        **metadata,
                    }
    except Exception as e:
        logger.warning("Failed to load integration credentials: %s", e)

    return credentials_map


def _integration_to_provider(integration_name: str) -> str:
    """Map integration name to credential provider name."""
    PROVIDER_MAP = {
        "google_calendar": "google_calendar",
        "linear": "linear",
    }
    return PROVIDER_MAP.get(integration_name, integration_name)

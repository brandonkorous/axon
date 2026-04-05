"""Zoom webhook endpoint — receives Team Chat events."""

from __future__ import annotations

import hashlib
import hmac

from fastapi import APIRouter, Request, Response

from axon.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Set during lifespan startup
_zoom_bot = None
_zoom_credentials: dict[str, tuple[str, str, str]] = {}  # org_id -> (account_id, client_id, client_secret)
_verification_token: str = ""


def set_zoom_bot(
    bot, credentials: dict[str, tuple[str, str, str]], verification_token: str = "",
) -> None:
    """Called during startup to register the bot and credentials."""
    global _zoom_bot, _zoom_credentials, _verification_token
    _zoom_bot = bot
    _zoom_credentials = credentials
    _verification_token = verification_token


@router.post("/events")
async def zoom_events(request: Request) -> Response:
    """Receive incoming events from Zoom webhooks.

    Handles URL validation challenge and team_chat.message_posted events.
    """
    try:
        body = await request.json()
    except Exception:
        return Response(status_code=400)

    # Handle Zoom URL validation challenge
    event_type = body.get("event", "")
    if event_type == "endpoint.url_validation":
        plain_token = body.get("payload", {}).get("plainToken", "")
        if plain_token and _verification_token:
            hash_value = hmac.new(
                _verification_token.encode(), plain_token.encode(), hashlib.sha256,
            ).hexdigest()
            return Response(
                content=f'{{"plainToken":"{plain_token}","encryptedToken":"{hash_value}"}}',
                media_type="application/json",
            )
        return Response(status_code=200)

    if not _zoom_bot:
        return Response(status_code=200)

    # Find credentials
    account_id, client_id, client_secret = "", "", ""
    for org_id, creds in _zoom_credentials.items():
        account_id, client_id, client_secret = creds
        if account_id:
            break

    if not account_id:
        return Response(status_code=200)

    try:
        await _zoom_bot.process_event(body, account_id, client_id, client_secret)
    except Exception:
        logger.exception("Error processing Zoom event")

    return Response(status_code=200)

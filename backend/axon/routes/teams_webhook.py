"""Microsoft Teams webhook endpoint — receives incoming bot messages."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request, Response

logger = logging.getLogger(__name__)

router = APIRouter()

# Set during lifespan startup
_teams_bot = None
_teams_credentials: dict[str, tuple[str, str]] = {}  # org_id -> (app_id, app_secret)


def set_teams_bot(bot, credentials: dict[str, tuple[str, str]]) -> None:
    """Called during startup to register the bot and credentials."""
    global _teams_bot, _teams_credentials
    _teams_bot = bot
    _teams_credentials = credentials


@router.post("/messages")
async def teams_messages(request: Request) -> Response:
    """Receive incoming activities from Microsoft Teams Bot Framework."""
    if not _teams_bot:
        return Response(status_code=200)

    try:
        activity = await request.json()
    except Exception:
        return Response(status_code=400)

    # Find credentials for this activity
    app_id, app_secret = "", ""
    for org_id, creds in _teams_credentials.items():
        app_id, app_secret = creds
        if app_id:
            break

    if not app_id:
        logger.warning("Teams webhook received but no credentials configured")
        return Response(status_code=200)

    try:
        await _teams_bot.process_activity(activity, app_id, app_secret)
    except Exception:
        logger.exception("Error processing Teams activity")

    return Response(status_code=200)

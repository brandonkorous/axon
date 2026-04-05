"""Zoom senders — Team Chat messages and meeting creation via Zoom API."""

from __future__ import annotations

import httpx

from axon.logging import get_logger

logger = get_logger(__name__)

ZOOM_AUTH_URL = "https://zoom.us/oauth/token"
ZOOM_API_BASE = "https://api.zoom.us/v2"


async def _get_zoom_token(account_id: str, client_id: str, client_secret: str) -> str:
    """Get an OAuth access token using server-to-server credentials."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            ZOOM_AUTH_URL,
            params={"grant_type": "account_credentials", "account_id": account_id},
            auth=(client_id, client_secret),
            timeout=10.0,
        )
    data = resp.json()
    return data.get("access_token", "")


async def send_zoom_chat(
    account_id: str,
    client_id: str,
    client_secret: str,
    channel_id: str,
    content: str,
) -> str:
    """Send a Zoom Team Chat message via the Zoom API.

    Returns a human-readable result string.
    """
    if not account_id or not client_id or not client_secret:
        return (
            "Error: Zoom credentials not configured. Add 'zoom_account_id', "
            "'zoom_client_id', and 'zoom_client_secret' credentials."
        )

    try:
        token = await _get_zoom_token(account_id, client_id, client_secret)
        if not token:
            return "Error: Failed to authenticate with Zoom."

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{ZOOM_API_BASE}/im/chat/messages",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={
                    "to_channel": channel_id,
                    "message": content,
                },
                timeout=10.0,
            )

        if resp.status_code in (200, 201):
            logger.info("Zoom chat sent to channel %s", channel_id)
            return f"Zoom chat message sent to channel {channel_id}."
        else:
            error = resp.text[:300]
            logger.error("Zoom API error %d: %s", resp.status_code, error)
            return f"Error sending Zoom chat: {resp.status_code} — {error}"
    except httpx.TimeoutException:
        return "Error: Zoom API request timed out."
    except Exception as e:
        logger.exception("Zoom chat send failed")
        return f"Error sending Zoom chat: {e}"


async def create_zoom_meeting(
    account_id: str,
    client_id: str,
    client_secret: str,
    topic: str,
    duration: int = 30,
    start_time: str = "",
) -> str:
    """Create a Zoom meeting and return the join URL.

    Returns a human-readable result with the meeting link.
    """
    if not account_id or not client_id or not client_secret:
        return (
            "Error: Zoom credentials not configured. Add 'zoom_account_id', "
            "'zoom_client_id', and 'zoom_client_secret' credentials."
        )

    try:
        token = await _get_zoom_token(account_id, client_id, client_secret)
        if not token:
            return "Error: Failed to authenticate with Zoom."

        meeting_data: dict = {
            "topic": topic,
            "type": 2 if start_time else 1,  # 1=instant, 2=scheduled
            "duration": duration,
            "settings": {
                "join_before_host": True,
                "waiting_room": False,
            },
        }
        if start_time:
            meeting_data["start_time"] = start_time
            meeting_data["timezone"] = "UTC"

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{ZOOM_API_BASE}/users/me/meetings",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=meeting_data,
                timeout=10.0,
            )

        if resp.status_code in (200, 201):
            data = resp.json()
            join_url = data.get("join_url", "")
            meeting_id = data.get("id", "")
            logger.info("Zoom meeting created: %s", meeting_id)
            return (
                f"Zoom meeting created successfully.\n"
                f"**Topic:** {topic}\n"
                f"**Join URL:** {join_url}\n"
                f"**Meeting ID:** {meeting_id}"
            )
        else:
            error = resp.text[:300]
            logger.error("Zoom meeting API error %d: %s", resp.status_code, error)
            return f"Error creating Zoom meeting: {resp.status_code} — {error}"
    except httpx.TimeoutException:
        return "Error: Zoom API request timed out."
    except Exception as e:
        logger.exception("Zoom meeting creation failed")
        return f"Error creating Zoom meeting: {e}"

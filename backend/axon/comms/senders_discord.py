"""Discord senders — Scheduled event creation via Discord REST API."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx

from axon.logging import get_logger

logger = get_logger(__name__)

DISCORD_API = "https://discord.com/api/v10"

# Guild Scheduled Event entity types
ENTITY_EXTERNAL = 3


async def create_discord_event(
    bot_token: str,
    guild_id: str,
    name: str,
    start_time: str,
    end_time: str = "",
    description: str = "",
    location: str = "",
) -> str:
    """Create a Discord Guild Scheduled Event.

    Uses entity type EXTERNAL so no voice channel is required.
    *start_time* and *end_time* must be ISO 8601 strings.
    If *end_time* is omitted, defaults to start_time + 1 hour.

    Returns a human-readable result with the event link.
    """
    if not bot_token:
        return "Error: Discord bot token not configured. Add a 'discord' credential."
    if not guild_id:
        return "Error: Discord guild ID not configured in org settings."

    try:
        # Default end_time to start + 1 hour if not provided
        if not end_time:
            try:
                dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                end_dt = dt + timedelta(hours=1)
                end_time = end_dt.isoformat()
            except ValueError:
                end_time = start_time  # fallback — API will validate

        event_data: dict = {
            "name": name,
            "scheduled_start_time": start_time,
            "scheduled_end_time": end_time,
            "privacy_level": 2,  # GUILD_ONLY
            "entity_type": ENTITY_EXTERNAL,
            "entity_metadata": {"location": location or "Online"},
        }
        if description:
            event_data["description"] = description

        url = f"{DISCORD_API}/guilds/{guild_id}/scheduled-events"
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                headers={
                    "Authorization": f"Bot {bot_token}",
                    "Content-Type": "application/json",
                },
                json=event_data,
                timeout=10.0,
            )

        if resp.status_code in (200, 201):
            data = resp.json()
            event_id = data.get("id", "")
            event_url = f"https://discord.com/events/{guild_id}/{event_id}"
            logger.info("Discord event created: %s", event_id)
            return (
                f"Discord event created successfully.\n"
                f"**Name:** {name}\n"
                f"**Start:** {start_time}\n"
                f"**Event URL:** {event_url}\n"
                f"**Event ID:** {event_id}"
            )
        else:
            error = resp.text[:300]
            logger.error("Discord API error %d: %s", resp.status_code, error)
            return f"Error creating Discord event: {resp.status_code} — {error}"
    except httpx.TimeoutException:
        return "Error: Discord API request timed out."
    except Exception as e:
        logger.exception("Discord event creation failed")
        return f"Error creating Discord event: {e}"

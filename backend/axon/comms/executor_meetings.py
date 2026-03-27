"""Meeting/event creation handlers — extracted from CommsToolExecutor."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from axon.org import OrgCommsConfig


async def handle_create_zoom_meeting(org_id: str, args: dict) -> str:
    """Create a Zoom meeting (not subject to approval — returns URL immediately)."""
    topic = args.get("topic", "")
    if not topic:
        return "Error: 'topic' is required."

    from axon.comms.credentials import resolve_credential
    from axon.comms.senders_zoom import create_zoom_meeting

    account_id = await resolve_credential(org_id, "zoom_account_id") or ""
    client_id = await resolve_credential(org_id, "zoom_client_id") or ""
    client_secret = await resolve_credential(org_id, "zoom_client_secret") or ""
    return await create_zoom_meeting(
        account_id, client_id, client_secret,
        topic=topic,
        duration=args.get("duration", 30),
        start_time=args.get("start_time", ""),
    )


async def handle_create_teams_meeting(
    org_id: str, config: "OrgCommsConfig", args: dict,
) -> str:
    """Create a Teams online meeting (not subject to approval)."""
    subject = args.get("subject", "")
    if not subject:
        return "Error: 'subject' is required."

    from axon.comms.credentials import resolve_credential
    from axon.comms.senders_teams import create_teams_meeting

    app_id = await resolve_credential(org_id, "teams_app_id") or ""
    app_secret = await resolve_credential(org_id, "teams_app_secret") or ""
    organizer_id = await resolve_credential(org_id, "teams_organizer_id") or ""
    tenant_id = config.teams.tenant_id if config.teams else ""
    return await create_teams_meeting(
        tenant_id, app_id, app_secret, organizer_id,
        subject=subject,
        duration=args.get("duration", 30),
        start_time=args.get("start_time", ""),
    )


async def handle_create_discord_event(
    org_id: str, config: "OrgCommsConfig", args: dict,
) -> str:
    """Create a Discord scheduled event (not subject to approval)."""
    name = args.get("name", "")
    start_time = args.get("start_time", "")
    if not name or not start_time:
        return "Error: 'name' and 'start_time' are required."

    from axon.comms.credentials import resolve_credential
    from axon.comms.senders_discord import create_discord_event

    bot_token = await resolve_credential(org_id, "discord") or ""
    guild_id = config.discord.guild_id if config.discord else ""
    return await create_discord_event(
        bot_token, guild_id,
        name=name,
        start_time=start_time,
        end_time=args.get("end_time", ""),
        description=args.get("description", ""),
        location=args.get("location", ""),
    )

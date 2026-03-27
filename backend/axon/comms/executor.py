"""CommsToolExecutor — handles comms_* tool calls from agents."""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from axon.comms.constants import APPROVAL_TYPE_COMMS, CommsChannel

if TYPE_CHECKING:
    from axon.org import OrgCommsConfig
    from axon.vault.vault import VaultManager

logger = logging.getLogger(__name__)


class CommsToolExecutor:
    """Executes comms tool calls — send email/discord, lookup contacts.

    Outbound messages are routed through approval (or sent directly) based
    on org-level require_approval setting.
    """

    def __init__(
        self,
        shared_vault: "VaultManager",
        agent_id: str,
        org_id: str,
        org_comms_config: "OrgCommsConfig",
        email_alias: str = "",
        agent_display_name: str = "",
    ):
        self.shared_vault = shared_vault
        self.agent_id = agent_id
        self.org_id = org_id
        self.config = org_comms_config
        self.from_name = email_alias or agent_id
        self.agent_display_name = agent_display_name

    async def execute(self, tool_name: str, arguments: str) -> str:
        """Execute a comms tool call and return the result."""
        try:
            args = json.loads(arguments)
        except json.JSONDecodeError:
            return f"Error: Invalid JSON arguments: {arguments}"

        handlers = {
            "comms_send_email": self._send_email,
            "comms_send_discord": self._send_discord,
            "comms_send_slack": self._send_slack,
            "comms_send_teams": self._send_teams,
            "comms_send_zoom": self._send_zoom,
            "comms_create_zoom_meeting": self._create_zoom_meeting,
            "comms_create_teams_meeting": self._create_teams_meeting,
            "comms_create_discord_event": self._create_discord_event,
            "comms_lookup_contact": self._lookup_contact,
        }

        handler = handlers.get(tool_name)
        if not handler:
            return f"Error: Unknown comms tool: {tool_name}"

        try:
            return await handler(args)
        except Exception as e:
            logger.exception("Comms tool error: %s", tool_name)
            return f"Error executing {tool_name}: {e}"

    async def _send_email(self, args: dict) -> str:
        """Queue or send an email."""
        to = args.get("to", "")
        subject = args.get("subject", "")
        body = args.get("body", "")
        cc = args.get("cc", "")

        if not to or not subject or not body:
            return "Error: 'to', 'subject', and 'body' are required."

        if self.config.require_approval:
            return await self._create_approval_task(
                channel=CommsChannel.EMAIL,
                payload={"to": to, "subject": subject, "body": body, "cc": cc},
                preview=f"**To:** {to}\n**Subject:** {subject}\n\n{body}",
            )

        from axon.comms.credentials import resolve_credential
        from axon.comms.senders import send_email
        api_key = await resolve_credential(self.org_id, "resend") or ""
        return await send_email(
            api_key, self.config.email_domain, to, subject, body, cc,
            self.from_name, self.config.email_signature, self.agent_display_name,
        )

    async def _send_discord(self, args: dict) -> str:
        """Queue or send a Discord message."""
        target = args.get("target", "")
        content = args.get("content", "")
        is_dm = args.get("is_dm", False)

        if not target or not content:
            return "Error: 'target' and 'content' are required."

        if not target.isdigit():
            # Try to resolve from channel mappings
            mappings = self.config.discord.channel_mappings if self.config.discord else {}
            available = ", ".join(f"{cid}" for cid in mappings) if mappings else "none configured"
            return (
                f"Error: '{target}' is not a valid Discord ID. "
                f"Discord requires a numeric snowflake ID (e.g. '1487175080776696089'). "
                f"Configured channels: {available}"
            )

        if self.config.require_approval:
            return await self._create_approval_task(
                channel=CommsChannel.DISCORD,
                payload={"target": target, "content": content, "is_dm": is_dm},
                preview=f"**To:** {'DM ' if is_dm else 'Channel '}{target}\n\n{content}",
            )

        from axon.comms.credentials import resolve_credential
        from axon.comms.senders import send_discord_message
        bot_token = await resolve_credential(self.org_id, "discord") or ""
        return await send_discord_message(bot_token, target, content, is_dm)

    async def _send_slack(self, args: dict) -> str:
        """Queue or send a Slack message."""
        channel = args.get("channel", "")
        content = args.get("content", "")

        if not channel or not content:
            return "Error: 'channel' and 'content' are required."

        if self.config.require_approval:
            return await self._create_approval_task(
                channel=CommsChannel.SLACK,
                payload={"channel": channel, "content": content},
                preview=f"**Channel:** {channel}\n\n{content}",
            )

        from axon.comms.credentials import resolve_credential
        from axon.comms.senders import send_slack_message
        bot_token = await resolve_credential(self.org_id, "slack_bot_token") or ""
        return await send_slack_message(bot_token, channel, content)

    async def _send_teams(self, args: dict) -> str:
        """Queue or send a Teams message."""
        channel = args.get("channel", "")
        content = args.get("content", "")

        if not channel or not content:
            return "Error: 'channel' and 'content' are required."

        if self.config.require_approval:
            return await self._create_approval_task(
                channel=CommsChannel.TEAMS,
                payload={"channel": channel, "content": content},
                preview=f"**Channel:** {channel}\n\n{content}",
            )

        from axon.comms.credentials import resolve_credential
        from axon.comms.senders import send_teams_message
        app_id = await resolve_credential(self.org_id, "teams_app_id") or ""
        app_secret = await resolve_credential(self.org_id, "teams_app_secret") or ""
        service_url = "https://smba.trafficmanager.net/amer/"
        return await send_teams_message(app_id, app_secret, service_url, channel, content)

    async def _send_zoom(self, args: dict) -> str:
        """Queue or send a Zoom Team Chat message."""
        channel = args.get("channel", "")
        content = args.get("content", "")

        if not channel or not content:
            return "Error: 'channel' and 'content' are required."

        if self.config.require_approval:
            return await self._create_approval_task(
                channel=CommsChannel.ZOOM,
                payload={"channel": channel, "content": content},
                preview=f"**Channel:** {channel}\n\n{content}",
            )

        from axon.comms.credentials import resolve_credential
        from axon.comms.senders_zoom import send_zoom_chat
        account_id = await resolve_credential(self.org_id, "zoom_account_id") or ""
        client_id = await resolve_credential(self.org_id, "zoom_client_id") or ""
        client_secret = await resolve_credential(self.org_id, "zoom_client_secret") or ""
        return await send_zoom_chat(account_id, client_id, client_secret, channel, content)

    async def _create_zoom_meeting(self, args: dict) -> str:
        from axon.comms.executor_meetings import handle_create_zoom_meeting
        return await handle_create_zoom_meeting(self.org_id, args)

    async def _create_teams_meeting(self, args: dict) -> str:
        from axon.comms.executor_meetings import handle_create_teams_meeting
        return await handle_create_teams_meeting(self.org_id, self.config, args)

    async def _create_discord_event(self, args: dict) -> str:
        from axon.comms.executor_meetings import handle_create_discord_event
        return await handle_create_discord_event(self.org_id, self.config, args)

    async def _create_approval_task(
        self, channel: CommsChannel, payload: dict, preview: str,
    ) -> str:
        """Create an awaiting_approval task in the shared vault."""
        today = str(date.today())
        slug = payload.get("to", payload.get("target", "unknown"))[:30]
        slug = slug.replace("@", "-at-").replace(".", "-")
        filename = f"tasks/{today}-comms-{channel.value}-{slug}.md"

        metadata: dict[str, Any] = {
            "name": f"Send {channel.value}: {payload.get('subject', payload.get('content', '')[:50])}",
            "type": APPROVAL_TYPE_COMMS,
            "status": "awaiting_approval",
            "channel": channel.value,
            "comms_payload": json.dumps(payload),
            "created_by": self.agent_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
        }

        body = f"## Outbound {channel.value.title()}\n\n{preview}"
        self.shared_vault.write_file(filename, metadata, body)

        recipient = payload.get("to", payload.get("target", "recipient"))
        logger.info("[%s] Comms approval queued: %s → %s", self.agent_id, channel.value, recipient)
        return f"{channel.value.title()} to {recipient} queued for approval."

    async def _lookup_contact(self, args: dict) -> str:
        from axon.comms.contacts import lookup_contact
        return await lookup_contact(self.shared_vault, args.get("query", ""))

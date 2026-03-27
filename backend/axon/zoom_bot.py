"""Zoom integration — Team Chat messaging and meeting creation.

Zoom uses OAuth server-to-server for API access. Inbound messages
arrive via webhook at /api/zoom/events. Outbound uses the Zoom REST API.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

import httpx

import axon.registry as registry

if TYPE_CHECKING:
    from axon.agents.agent import Agent
    from axon.org import OrgInstance

logger = logging.getLogger("axon.zoom")

ZOOM_AUTH_URL = "https://zoom.us/oauth/token"
ZOOM_API_BASE = "https://api.zoom.us/v2"


class ZoomTokenCache:
    """Caches OAuth tokens for the Zoom API."""

    def __init__(self) -> None:
        self._token: str = ""
        self._expires_at: float = 0

    async def get_token(self, account_id: str, client_id: str, client_secret: str) -> str:
        import time
        if self._token and time.time() < self._expires_at - 60:
            return self._token

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                ZOOM_AUTH_URL,
                params={"grant_type": "account_credentials", "account_id": account_id},
                auth=(client_id, client_secret),
                timeout=10.0,
            )
        data = resp.json()
        self._token = data.get("access_token", "")
        self._expires_at = time.time() + data.get("expires_in", 3600)
        return self._token


_token_cache = ZoomTokenCache()


class AxonZoomBot:
    """Processes incoming Zoom Team Chat events and routes to Axon agents."""

    def __init__(self, channel_org_map: dict[str, tuple[str, str]]):
        self.channel_org_map = channel_org_map

    async def process_event(
        self, event: dict[str, Any],
        account_id: str, client_id: str, client_secret: str,
    ) -> None:
        """Process an incoming Zoom Team Chat event."""
        event_type = event.get("event", "")
        if event_type != "team_chat.message_posted":
            return

        payload = event.get("payload", {}).get("object", {})
        channel_id = payload.get("channel_id", "")
        message = payload.get("message", "")
        robot_jid = payload.get("robot_jid", "")

        # Ignore messages from the bot itself
        sender = payload.get("sender", "")
        if sender == robot_jid:
            return

        if not message or not channel_id:
            return

        if channel_id not in self.channel_org_map:
            return

        org_id, agent_id = self.channel_org_map[channel_id]
        org = registry.org_registry.get(org_id)
        if not org:
            return

        # Check for @agent_name prefix
        text = message.strip()
        if text.startswith("@"):
            parts = text.split(None, 1)
            mentioned_name = parts[0][1:].lower()
            if mentioned_name in org.agent_registry:
                agent_id = mentioned_name
                text = parts[1] if len(parts) > 1 else ""

        if not text:
            return

        token = await _token_cache.get_token(account_id, client_id, client_secret)

        if agent_id == "huddle":
            await self._route_huddle(channel_id, robot_jid, token, org, text)
        else:
            await self._route_agent(channel_id, robot_jid, token, org, agent_id, text)

    async def _route_agent(
        self, channel_id: str, robot_jid: str, token: str,
        org: "OrgInstance", agent_id: str, content: str,
    ) -> None:
        agent = org.agent_registry.get(agent_id)
        if not agent:
            await _send_chat(token, robot_jid, channel_id, f"Agent `{agent_id}` not found.")
            return

        sender_name = payload.get("sender", "unknown") if hasattr(self, '_last_payload') else "unknown"
        contextualized = (
            f"[Message from Zoom Team Chat — channel: {channel_id}]\n\n{content}"
        )

        response = await _collect_agent_response(agent, contextualized)
        if not response.strip():
            response = f"*{agent.name} had no response.*"

        prefix = f"**{agent.name}:**\n" if agent_id != "axon" else ""
        await _send_chat(token, robot_jid, channel_id, f"{prefix}{response}")

    async def _route_huddle(
        self, channel_id: str, robot_jid: str, token: str,
        org: "OrgInstance", content: str,
    ) -> None:
        advisors = {aid: a for aid, a in org.agent_registry.items() if aid != "axon"}
        if not advisors:
            advisors = org.agent_registry

        contextualized = f"[Message from Zoom Team Chat]\n\n{content}"
        tasks = {
            aid: asyncio.create_task(_collect_agent_response(agent, contextualized))
            for aid, agent in advisors.items()
        }
        for aid, task in tasks.items():
            agent = advisors[aid]
            try:
                text = await task
            except Exception as e:
                logger.error(f"Huddle advisor {aid} failed: {e}")
                text = "*unavailable*"
            if text.strip():
                await _send_chat(token, robot_jid, channel_id, f"**{agent.name}:**\n{text}")


async def _collect_agent_response(agent: "Agent", content: str) -> str:
    full_response = ""
    async for chunk in agent.process(content):
        if chunk.type == "text":
            full_response += chunk.content
    return full_response


async def _send_chat(token: str, robot_jid: str, channel_id: str, message: str) -> None:
    """Send a message to a Zoom Team Chat channel."""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{ZOOM_API_BASE}/im/chat/messages",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={
                    "robot_jid": robot_jid,
                    "to_channel": channel_id,
                    "content": {"body": [{"type": "text", "text": message}]},
                },
                timeout=10.0,
            )
    except Exception as e:
        logger.error(f"Zoom chat send failed: {e}")


def build_channel_map() -> dict[str, tuple[str, str]]:
    """Build the channel -> (org_id, agent_id) mapping from all orgs."""
    channel_map: dict[str, tuple[str, str]] = {}
    for org_id, org in registry.org_registry.items():
        zoom_config = org.config.comms.zoom
        if not zoom_config or not zoom_config.channel_mappings:
            continue
        for channel_id, agent_id in zoom_config.channel_mappings.items():
            channel_map[channel_id] = (org_id, agent_id)
    return channel_map


def create_zoom_bot() -> AxonZoomBot | None:
    """Create a Zoom bot if any org has Zoom configured."""
    channel_map = build_channel_map()
    if not channel_map:
        return None
    logger.info(f"Zoom bot initialized with {len(channel_map)} channel mapping(s)")
    print(f"[AXON] Zoom bot initialized with {len(channel_map)} channel mapping(s)")
    return AxonZoomBot(channel_map)

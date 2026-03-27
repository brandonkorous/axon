"""Microsoft Teams integration — talk to Axon agents from Teams.

Teams uses a webhook model: incoming messages arrive at a FastAPI endpoint,
and responses are sent back via the Bot Framework REST API.
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

logger = logging.getLogger("axon.teams")

# Bot Framework endpoints
LOGIN_URL = "https://login.microsoftonline.com/botframework.com/oauth2/v2.0/token"
BOT_SCOPE = "https://api.botframework.com/.default"


class TeamsTokenCache:
    """Caches OAuth tokens for the Bot Framework API."""

    def __init__(self) -> None:
        self._token: str = ""
        self._expires_at: float = 0

    async def get_token(self, app_id: str, app_secret: str) -> str:
        """Get a valid access token, refreshing if expired."""
        import time
        if self._token and time.time() < self._expires_at - 60:
            return self._token

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                LOGIN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": app_id,
                    "client_secret": app_secret,
                    "scope": BOT_SCOPE,
                },
                timeout=10.0,
            )
        data = resp.json()
        self._token = data.get("access_token", "")
        self._expires_at = time.time() + data.get("expires_in", 3600)
        return self._token


_token_cache = TeamsTokenCache()


class AxonTeamsBot:
    """Processes incoming Teams activities and routes to Axon agents."""

    def __init__(self, channel_org_map: dict[str, tuple[str, str]]):
        self.channel_org_map = channel_org_map

    async def process_activity(
        self, activity: dict[str, Any], app_id: str, app_secret: str,
    ) -> None:
        """Process an incoming Teams activity (message)."""
        if activity.get("type") != "message":
            return

        text = (activity.get("text") or "").strip()
        channel_id = activity.get("channelData", {}).get("teamsChannelId", "")
        conversation = activity.get("conversation", {})
        service_url = activity.get("serviceUrl", "")
        conv_id = conversation.get("id", "")

        # Strip bot @mention from text
        if activity.get("entities"):
            for entity in activity["entities"]:
                if entity.get("type") == "mention" and entity.get("mentioned", {}).get("role") == "bot":
                    mention_text = entity.get("text", "")
                    text = text.replace(mention_text, "").strip()

        if not text:
            return

        # Look up channel mapping
        lookup_id = channel_id or conv_id
        if lookup_id not in self.channel_org_map:
            return

        org_id, agent_id = self.channel_org_map[lookup_id]
        org = registry.org_registry.get(org_id)
        if not org:
            return

        # Check for @agent_name prefix
        if text.startswith("@"):
            parts = text.split(None, 1)
            mentioned_name = parts[0][1:].lower()
            if mentioned_name in org.agent_registry:
                agent_id = mentioned_name
                text = parts[1] if len(parts) > 1 else ""

        if not text:
            return

        token = await _token_cache.get_token(app_id, app_secret)

        if agent_id == "huddle":
            await self._route_huddle(service_url, conv_id, activity, token, org, text)
        else:
            await self._route_agent(service_url, conv_id, activity, token, org, agent_id, text)

    async def _route_agent(
        self, service_url: str, conv_id: str, activity: dict,
        token: str, org: "OrgInstance", agent_id: str, content: str,
    ) -> None:
        agent = org.agent_registry.get(agent_id)
        if not agent:
            await self._reply(service_url, conv_id, activity, token, f"Agent `{agent_id}` not found.")
            return

        sender = activity.get("from", {}).get("name", "unknown")
        contextualized = (
            f"[Message from Microsoft Teams — user: {sender}]\n\n{content}"
        )

        response = await _collect_agent_response(agent, contextualized)
        if not response.strip():
            response = f"*{agent.name} had no response.*"

        prefix = f"**{agent.name}:**\n" if agent_id != "axon" else ""
        await self._reply(service_url, conv_id, activity, token, f"{prefix}{response}")

    async def _route_huddle(
        self, service_url: str, conv_id: str, activity: dict,
        token: str, org: "OrgInstance", content: str,
    ) -> None:
        advisors = {aid: a for aid, a in org.agent_registry.items() if aid != "axon"}
        if not advisors:
            advisors = org.agent_registry

        contextualized = f"[Message from Microsoft Teams]\n\n{content}"
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
                await self._reply(service_url, conv_id, activity, token, f"**{agent.name}:**\n{text}")

    @staticmethod
    async def _reply(
        service_url: str, conv_id: str, activity: dict,
        token: str, text: str,
    ) -> None:
        """Send a reply to a Teams conversation."""
        reply_url = f"{service_url}v3/conversations/{conv_id}/activities"
        payload = {
            "type": "message",
            "text": text,
            "replyToId": activity.get("id"),
            "conversation": activity.get("conversation"),
        }
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    reply_url,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=10.0,
                )
        except Exception as e:
            logger.error(f"Teams reply failed: {e}")


async def _collect_agent_response(agent: "Agent", content: str) -> str:
    full_response = ""
    async for chunk in agent.process(content):
        if chunk.type == "text":
            full_response += chunk.content
    return full_response


def build_channel_map() -> dict[str, tuple[str, str]]:
    """Build the channel -> (org_id, agent_id) mapping from all orgs."""
    channel_map: dict[str, tuple[str, str]] = {}
    for org_id, org in registry.org_registry.items():
        teams_config = org.config.comms.teams
        if not teams_config or not teams_config.channel_mappings:
            continue
        for channel_id, agent_id in teams_config.channel_mappings.items():
            channel_map[channel_id] = (org_id, agent_id)
    return channel_map


def create_teams_bot() -> AxonTeamsBot | None:
    """Create a Teams bot if any org has Teams configured."""
    channel_map = build_channel_map()
    if not channel_map:
        return None

    logger.info(f"Teams bot initialized with {len(channel_map)} channel mapping(s)")
    print(f"[AXON] Teams bot initialized with {len(channel_map)} channel mapping(s)")
    return AxonTeamsBot(channel_map)

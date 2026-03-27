"""Slack integration — talk to Axon agents from Slack via Socket Mode."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_sdk.web.async_client import AsyncWebClient

import axon.registry as registry

if TYPE_CHECKING:
    from axon.agents.agent import Agent
    from axon.org import OrgInstance

logger = logging.getLogger("axon.slack")

MAX_SLACK_LENGTH = 3000  # Slack's practical message limit


def _split_message(text: str) -> list[str]:
    """Split a message into chunks that fit within Slack's limit."""
    if len(text) <= MAX_SLACK_LENGTH:
        return [text]

    chunks: list[str] = []
    while text:
        if len(text) <= MAX_SLACK_LENGTH:
            chunks.append(text)
            break
        cut = text.rfind("\n", 0, MAX_SLACK_LENGTH)
        if cut == -1:
            cut = text.rfind(" ", 0, MAX_SLACK_LENGTH)
        if cut == -1:
            cut = MAX_SLACK_LENGTH
        chunks.append(text[:cut])
        text = text[cut:].lstrip("\n")

    return chunks


class AxonSlackBot:
    """Slack bot that routes messages to Axon agents via Socket Mode."""

    def __init__(
        self,
        bot_token: str,
        app_token: str,
        channel_org_map: dict[str, tuple[str, str]],
    ):
        self.channel_org_map = channel_org_map
        self.app = AsyncApp(token=bot_token)
        self.handler = AsyncSocketModeHandler(self.app, app_token)
        self.client = AsyncWebClient(token=bot_token)
        self._bot_user_id: str = ""

        # Register event handlers
        self.app.event("message")(self._handle_message)

    async def start(self) -> None:
        """Start the Socket Mode connection."""
        auth = await self.client.auth_test()
        self._bot_user_id = auth["user_id"]
        logger.info(f"Slack bot connected as {auth['user']} ({self._bot_user_id})")
        print(f"[AXON] Slack bot connected as {auth['user']}")
        await self.handler.start_async()

    async def close(self) -> None:
        """Disconnect from Slack."""
        await self.handler.close_async()

    async def _handle_message(self, event: dict, say) -> None:
        """Handle incoming Slack messages."""
        # Ignore bot messages and message edits
        if event.get("bot_id") or event.get("subtype"):
            return

        user = event.get("user", "")
        if user == self._bot_user_id:
            return

        channel = event.get("channel", "")
        text = (event.get("text") or "").strip()

        # Strip bot mention if present
        mention = f"<@{self._bot_user_id}>"
        if mention in text:
            text = text.replace(mention, "").strip()

        if not text:
            return

        # Check if this channel is mapped
        if channel not in self.channel_org_map:
            # Only respond if directly mentioned in unmapped channel
            if mention not in (event.get("text") or ""):
                return
            org = registry.get_default_org()
            if not org:
                return
            await self._route_and_respond(channel, event, org, "axon", text)
            return

        org_id, default_agent_id = self.channel_org_map[channel]
        org = registry.org_registry.get(org_id)
        if not org:
            return

        # Check for @agent_name prefix
        agent_id = default_agent_id
        if text.startswith("@"):
            parts = text.split(None, 1)
            mentioned_name = parts[0][1:].lower()
            if mentioned_name in org.agent_registry:
                agent_id = mentioned_name
                text = parts[1] if len(parts) > 1 else ""

        if not text:
            return

        await self._route_and_respond(channel, event, org, agent_id, text)

    async def _route_and_respond(
        self,
        channel: str,
        event: dict,
        org: "OrgInstance",
        agent_id: str,
        content: str,
    ) -> None:
        """Route a message to an agent and post the response as a thread reply."""
        thread_ts = event.get("thread_ts") or event.get("ts")

        if agent_id == "huddle":
            await self._route_huddle(channel, thread_ts, org, content)
            return

        agent = org.agent_registry.get(agent_id)
        if not agent:
            await self.client.chat_postMessage(
                channel=channel,
                thread_ts=thread_ts,
                text=f"Agent `{agent_id}` not found.",
            )
            return

        user_name = event.get("user", "unknown")
        contextualized = (
            f"[Message from Slack — channel: {channel}, "
            f"user: {user_name}]\n\n{content}"
        )

        full_response = await self._collect_agent_response(agent, contextualized)
        if not full_response.strip():
            full_response = f"_{agent.name} had no response._"

        prefix = f"*{agent.name}:*\n" if agent_id != "axon" else ""
        await self._send_response(channel, thread_ts, f"{prefix}{full_response}")

    async def _route_huddle(
        self,
        channel: str,
        thread_ts: str,
        org: "OrgInstance",
        content: str,
    ) -> None:
        """Route a message to all advisors (huddle mode)."""
        advisors = {
            aid: agent for aid, agent in org.agent_registry.items()
            if aid != "axon"
        }
        if not advisors:
            advisors = org.agent_registry

        contextualized = f"[Message from Slack — channel: {channel}]\n\n{content}"
        tasks = {
            aid: asyncio.create_task(self._collect_agent_response(agent, contextualized))
            for aid, agent in advisors.items()
        }
        results: list[tuple[str, str, str]] = []
        for aid, task in tasks.items():
            agent = advisors[aid]
            try:
                text = await task
                results.append((aid, agent.name, text))
            except Exception as e:
                logger.error(f"Huddle advisor {aid} failed: {e}")
                results.append((aid, agent.name, "_unavailable_"))

        for _, name, text in results:
            if not text.strip():
                continue
            response = f"*{name}:*\n{text}"
            await self._send_response(channel, thread_ts, response)

    @staticmethod
    async def _collect_agent_response(agent: "Agent", content: str) -> str:
        """Collect the full text response from an agent."""
        full_response = ""
        async for chunk in agent.process(content):
            if chunk.type == "text":
                full_response += chunk.content
        return full_response

    async def _send_response(
        self, channel: str, thread_ts: str, text: str,
    ) -> None:
        """Send a (potentially long) response as a thread reply."""
        for chunk in _split_message(text):
            await self.client.chat_postMessage(
                channel=channel,
                thread_ts=thread_ts,
                text=chunk,
            )


def build_channel_map() -> dict[str, tuple[str, str]]:
    """Build the channel -> (org_id, agent_id) mapping from all orgs."""
    channel_map: dict[str, tuple[str, str]] = {}

    for org_id, org in registry.org_registry.items():
        slack_config = org.config.comms.slack
        if not slack_config or not slack_config.channel_mappings:
            continue

        for channel_id, agent_id in slack_config.channel_mappings.items():
            channel_map[channel_id] = (org_id, agent_id)

    return channel_map


async def get_slack_tokens() -> tuple[str, str] | None:
    """Get Slack bot token and app token from any org's credential DB.

    Returns (bot_token, app_token) or None.
    """
    from axon.comms.credentials import resolve_credential

    for org_id, org in registry.org_registry.items():
        if org.config.comms.slack:
            bot_token = await resolve_credential(org_id, "slack_bot_token")
            app_token = await resolve_credential(org_id, "slack_app_token")
            if bot_token and app_token:
                return bot_token, app_token
    return None


async def start_slack_bot() -> AxonSlackBot | None:
    """Start the Slack bot if any org has Slack configured.

    Returns the bot instance (or None if no config found).
    """
    tokens = await get_slack_tokens()
    if not tokens:
        return None

    bot_token, app_token = tokens
    channel_map = build_channel_map()
    if not channel_map:
        logger.info("Slack tokens found but no channel mappings configured")
        return None

    bot = AxonSlackBot(bot_token, app_token, channel_map)

    logger.info(f"Starting Slack bot with {len(channel_map)} channel mapping(s)")
    print(f"[AXON] Starting Slack bot with {len(channel_map)} channel mapping(s)")

    asyncio.create_task(bot.start())
    return bot

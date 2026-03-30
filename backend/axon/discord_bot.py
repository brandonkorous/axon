"""Discord integration — talk to Axon agents from Discord."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import discord

import axon.registry as registry

if TYPE_CHECKING:
    from axon.agents.agent import Agent
    from axon.org import OrgInstance

logger = logging.getLogger("axon.discord")

MAX_DISCORD_LENGTH = 2000


def _split_message(text: str) -> list[str]:
    """Split a message into chunks that fit within Discord's 2000-char limit."""
    if len(text) <= MAX_DISCORD_LENGTH:
        return [text]

    chunks: list[str] = []
    while text:
        if len(text) <= MAX_DISCORD_LENGTH:
            chunks.append(text)
            break

        # Try to split at a newline
        cut = text.rfind("\n", 0, MAX_DISCORD_LENGTH)
        if cut == -1:
            # Fall back to space
            cut = text.rfind(" ", 0, MAX_DISCORD_LENGTH)
        if cut == -1:
            # Hard cut
            cut = MAX_DISCORD_LENGTH

        chunks.append(text[:cut])
        text = text[cut:].lstrip("\n")

    return chunks


class AxonDiscordBot(discord.Client):
    """Discord bot that routes messages to Axon agents."""

    def __init__(self, channel_org_map: dict[str, tuple[str, str]]):
        """Initialize the bot.

        Args:
            channel_org_map: Mapping of channel_id -> (org_id, agent_id).
                Built from each org's discord.channel_mappings config.
        """
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)

        # channel_id -> (org_id, default_agent_id)
        self.channel_org_map = channel_org_map

    def reload_channel_map(self) -> None:
        """Reload channel mappings from all orgs (call after config changes)."""
        new_map = build_channel_map()
        old_count = len(self.channel_org_map)
        self.channel_org_map = new_map
        logger.info("Discord channel map reloaded: %d → %d mappings", old_count, len(new_map))
        print(f"[AXON] Discord channel map reloaded: {len(new_map)} mapping(s)")

    async def on_ready(self) -> None:
        logger.info(f"Discord bot connected as {self.user}")
        print(f"[AXON] Discord bot connected as {self.user}")

    async def on_message(self, message: discord.Message) -> None:
        # Ignore own messages
        if message.author == self.user:
            return

        channel_id = str(message.channel.id)
        content = message.content.strip()

        # Check if this channel is mapped
        if channel_id not in self.channel_org_map:
            # Also check for @mentions in any channel
            if self.user and self.user.mentioned_in(message):
                # Remove the mention and try to route
                content = content.replace(f"<@{self.user.id}>", "").strip()
                if not content:
                    return
                # Use default org
                org = registry.get_default_org()
                if not org:
                    return
                await self._route_and_respond(message, org, "axon", content)
            return

        org_id, default_agent_id = self.channel_org_map[channel_id]
        org = registry.org_registry.get(org_id)
        if not org:
            logger.warning(f"Org {org_id} not found for channel {channel_id}")
            return

        # Determine target agent from @mention or prefix
        agent_id = default_agent_id
        if content.startswith("@"):
            # Parse @agent_name from the start of the message
            parts = content.split(None, 1)
            mentioned_name = parts[0][1:].lower()  # strip @

            # Check if it matches an agent in the org
            if mentioned_name in org.agent_registry:
                agent_id = mentioned_name
                content = parts[1] if len(parts) > 1 else ""
            elif self.user and f"<@{self.user.id}>" in parts[0]:
                # Discord mention format — strip it
                content = content.replace(f"<@{self.user.id}>", "").strip()

        if not content:
            return

        await self._route_and_respond(message, org, agent_id, content)

    async def _route_and_respond(
        self,
        message: discord.Message,
        org: "OrgInstance",
        agent_id: str,
        content: str,
    ) -> None:
        """Route a message to an agent and post the response as a thread reply."""
        if agent_id == "huddle":
            await self._route_huddle(message, org, content)
            return

        agent = org.agent_registry.get(agent_id)
        if not agent:
            await message.reply(f"Agent `{agent_id}` not found.", mention_author=False)
            return

        # Prefix with source context so the agent knows where the message came from
        channel_name = getattr(message.channel, "name", "unknown")
        author_name = message.author.display_name or message.author.name
        contextualized = (
            f"[Message from Discord — channel: #{channel_name}, "
            f"user: {author_name}]\n\n{content}"
        )

        # Show typing indicator while processing
        async with message.channel.typing():
            full_response = await self._collect_agent_response(agent, contextualized)

        if not full_response.strip():
            full_response = f"*{agent.name} had no response.*"

        await self._send_response(message, full_response, agent.name if agent_id != "axon" else "")

    async def _route_huddle(
        self,
        message: discord.Message,
        org: "OrgInstance",
        content: str,
    ) -> None:
        """Route a message to all advisors in the org (huddle mode)."""
        if not org.agent_registry:
            await message.reply("No agents available.", mention_author=False)
            return

        # Filter to non-axon agents (advisors only)
        advisors = {
            aid: agent for aid, agent in org.agent_registry.items()
            if aid != "axon"
        }
        if not advisors:
            advisors = org.agent_registry

        channel_name = getattr(message.channel, "name", "unknown")
        author_name = message.author.display_name or message.author.name
        contextualized = (
            f"[Message from Discord — channel: #{channel_name}, "
            f"user: {author_name}]\n\n{content}"
        )

        async with message.channel.typing():
            # Run all advisors concurrently
            tasks = {
                aid: asyncio.create_task(self._collect_agent_response(agent, contextualized))
                for aid, agent in advisors.items()
            }
            results: list[tuple[str, str, str]] = []  # (aid, name, text)
            for aid, task in tasks.items():
                agent = advisors[aid]
                try:
                    text = await task
                    results.append((aid, agent.name, text))
                except Exception as e:
                    logger.error(f"Huddle advisor {aid} failed: {e}")
                    results.append((aid, agent.name, "*unavailable*"))

        if not results:
            await message.reply("*No advisors responded.*", mention_author=False)
            return

        # Post each advisor's response as a separate message
        reply = None
        for _, name, text in results:
            if not text.strip():
                continue
            response = f"**{name}:**\n{text}"
            chunks = _split_message(response)
            if reply is None:
                reply = await message.reply(chunks[0], mention_author=False)
            else:
                await message.channel.send(chunks[0], reference=reply)
            for chunk in chunks[1:]:
                await message.channel.send(chunk, reference=reply)

    @staticmethod
    async def _collect_agent_response(agent: "Agent", content: str) -> str:
        """Collect the full text response from an agent."""
        full_response = ""
        async for chunk in agent.process(content):
            if chunk.type == "text":
                full_response += chunk.content
        return full_response

    async def _send_response(
        self,
        message: discord.Message,
        full_response: str,
        speaker_name: str = "",
    ) -> None:
        """Send a (potentially long) response as a reply with chunking."""
        chunks = _split_message(full_response)

        prefix = f"**{speaker_name}:** " if speaker_name else ""
        first_msg = f"{prefix}{chunks[0]}" if prefix else chunks[0]

        if len(first_msg) > MAX_DISCORD_LENGTH:
            first_chunks = _split_message(first_msg)
            reply = await message.reply(first_chunks[0], mention_author=False)
            for c in first_chunks[1:]:
                await message.channel.send(c, reference=reply)
        else:
            reply = await message.reply(first_msg, mention_author=False)

        for chunk in chunks[1:]:
            await message.channel.send(chunk, reference=reply)


def build_channel_map() -> dict[str, tuple[str, str]]:
    """Build the channel -> (org_id, agent_id) mapping from all orgs."""
    channel_map: dict[str, tuple[str, str]] = {}

    for org_id, org in registry.org_registry.items():
        discord_config = org.config.comms.discord or org.config.discord
        if not discord_config or not discord_config.channel_mappings:
            continue

        for channel_id, agent_id in discord_config.channel_mappings.items():
            channel_map[channel_id] = (org_id, agent_id)

    return channel_map


async def get_bot_token() -> str | None:
    """Get the Discord bot token from any org's credential DB."""
    from axon.comms.credentials import resolve_credential

    for org_id in registry.org_registry:
        token = await resolve_credential(org_id, "discord")
        if token:
            return token
    return None


async def start_discord_bot() -> AxonDiscordBot | None:
    """Start the Discord bot if any org has Discord configured.

    Returns the bot instance (or None if no config found).
    The bot runs as a background task.
    """
    token = await get_bot_token()
    if not token:
        print("[AXON] Discord: no bot token found in credentials")
        return None

    channel_map = build_channel_map()
    if not channel_map:
        print("[AXON] Discord: token found but no channel mappings configured")
        return None

    bot = AxonDiscordBot(channel_map)

    logger.info(f"Starting Discord bot with {len(channel_map)} channel mapping(s)")
    print(f"[AXON] Starting Discord bot with {len(channel_map)} channel mapping(s)")

    async def _supervised_start() -> None:
        """Run the bot with error logging — prevents silent task death."""
        try:
            await bot.start(token)
        except Exception:
            logger.exception("Discord bot crashed — will not auto-restart")

    # Start in background — don't block the server
    asyncio.create_task(_supervised_start())

    return bot

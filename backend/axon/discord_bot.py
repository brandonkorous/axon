"""Discord integration — talk to Axon agents from Discord."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import TYPE_CHECKING

import discord

import axon.registry as registry

if TYPE_CHECKING:
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
        agent = org.agent_registry.get(agent_id)
        if not agent:
            await message.reply(f"Agent `{agent_id}` not found.", mention_author=False)
            return

        # Show typing indicator while processing
        async with message.channel.typing():
            # Collect the full response
            full_response = ""
            try:
                async for chunk in agent.process(content):
                    if chunk.type == "text":
                        full_response += chunk.content
            except Exception as e:
                logger.error(f"Error processing message for {agent_id}: {e}")
                await message.reply(
                    f"Error from **{agent.name}**: {e}",
                    mention_author=False,
                )
                return

        if not full_response.strip():
            full_response = f"*{agent.name} had no response.*"

        # Post response — use thread if in a text channel, reply otherwise
        chunks = _split_message(full_response)

        # First chunk as a reply
        prefix = f"**{agent.name}:** " if agent_id != "axon" else ""
        first_msg = f"{prefix}{chunks[0]}" if prefix else chunks[0]

        # Trim prefix+content if it exceeds limit
        if len(first_msg) > MAX_DISCORD_LENGTH:
            first_chunks = _split_message(first_msg)
            reply = await message.reply(first_chunks[0], mention_author=False)
            for c in first_chunks[1:]:
                await message.channel.send(c, reference=reply)
        else:
            reply = await message.reply(first_msg, mention_author=False)

        # Remaining chunks as follow-ups
        for chunk in chunks[1:]:
            await message.channel.send(chunk, reference=reply)


def build_channel_map() -> dict[str, tuple[str, str]]:
    """Build the channel -> (org_id, agent_id) mapping from all orgs."""
    channel_map: dict[str, tuple[str, str]] = {}

    for org_id, org in registry.org_registry.items():
        discord_config = org.config.discord
        if not discord_config or not discord_config.channel_mappings:
            continue

        for channel_id, agent_id in discord_config.channel_mappings.items():
            channel_map[channel_id] = (org_id, agent_id)

    return channel_map


def get_bot_token() -> str | None:
    """Get the Discord bot token from any org's config."""
    for org in registry.org_registry.values():
        discord_config = org.config.discord
        if discord_config and discord_config.bot_token_env:
            token = os.environ.get(discord_config.bot_token_env)
            if token:
                return token
    return None


async def start_discord_bot() -> AxonDiscordBot | None:
    """Start the Discord bot if any org has Discord configured.

    Returns the bot instance (or None if no config found).
    The bot runs as a background task.
    """
    token = get_bot_token()
    if not token:
        return None

    channel_map = build_channel_map()
    if not channel_map:
        logger.info("Discord token found but no channel mappings configured")
        return None

    bot = AxonDiscordBot(channel_map)

    logger.info(f"Starting Discord bot with {len(channel_map)} channel mapping(s)")
    print(f"[AXON] Starting Discord bot with {len(channel_map)} channel mapping(s)")

    # Start in background — don't block the server
    asyncio.create_task(bot.start(token))

    return bot

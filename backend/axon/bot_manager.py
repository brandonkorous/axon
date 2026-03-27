"""Bot manager — tracks running bots and supports hot-start on credential changes."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger("axon.bot_manager")

# Module-level references to running bot instances
_discord_bot: Any = None
_slack_bot: Any = None

# Providers that should trigger a bot restart when credentials change
DISCORD_PROVIDERS = {"discord"}
SLACK_PROVIDERS = {"slack_bot_token", "slack_app_token"}


def set_discord_bot(bot: Any) -> None:
    global _discord_bot
    _discord_bot = bot


def set_slack_bot(bot: Any) -> None:
    global _slack_bot
    _slack_bot = bot


async def on_credential_changed(provider: str) -> None:
    """Called when a credential is created/updated/deleted.

    If the credential is for a bot integration, attempt to start or restart it.
    """
    if provider in DISCORD_PROVIDERS:
        await _try_start_discord()
    elif provider in SLACK_PROVIDERS:
        await _try_start_slack()


async def _try_start_discord() -> None:
    """Start the Discord bot, or reload its channel map if already running."""
    global _discord_bot
    if _discord_bot is not None:
        # Bot is running — reload channel mappings to pick up new org configs
        try:
            _discord_bot.reload_channel_map()
        except Exception as e:
            logger.error("Discord channel map reload failed: %s", e)
        return

    try:
        from axon.discord_bot import start_discord_bot
        bot = await start_discord_bot()
        if bot:
            _discord_bot = bot
            logger.info("Discord bot hot-started successfully")
    except ImportError:
        logger.warning("discord.py not installed — cannot hot-start")
    except Exception as e:
        logger.error("Discord bot hot-start failed: %s", e)


async def _try_start_slack() -> None:
    """Start the Slack bot if it's not already running."""
    global _slack_bot
    if _slack_bot is not None:
        logger.info("Slack bot already running, skipping hot-start")
        return

    try:
        from axon.slack_bot import start_slack_bot
        bot = await start_slack_bot()
        if bot:
            _slack_bot = bot
            logger.info("Slack bot hot-started successfully")
    except ImportError:
        logger.warning("slack_bolt not installed — cannot hot-start")
    except Exception as e:
        logger.error("Slack bot hot-start failed: %s", e)


async def on_config_changed(comms_update: Any = None) -> None:
    """Called when any org comms config is updated.

    Reloads channel maps on all running bots so changes are picked up immediately.
    """
    if _discord_bot is not None:
        try:
            _discord_bot.reload_channel_map()
        except Exception as e:
            logger.error("Discord channel map reload failed: %s", e)


async def shutdown() -> None:
    """Gracefully shut down all running bots."""
    global _discord_bot, _slack_bot
    if _discord_bot:
        await _discord_bot.close()
        _discord_bot = None
    if _slack_bot:
        try:
            await _slack_bot.close()
        except Exception:
            pass
        _slack_bot = None

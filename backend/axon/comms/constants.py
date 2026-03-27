"""Comms constants and enums."""

from __future__ import annotations

from enum import Enum


class CommsChannel(str, Enum):
    """Supported communication channels."""

    EMAIL = "email"
    DISCORD = "discord"
    SLACK = "slack"
    TEAMS = "teams"
    ZOOM = "zoom"


# Prefix for all comms tool names (used for routing in ToolExecutor)
COMMS_TOOL_PREFIX = "comms_"

# Approval task type for outbound messages
APPROVAL_TYPE_COMMS = "comms_outbound"

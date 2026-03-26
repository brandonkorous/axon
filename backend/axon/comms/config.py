"""Per-agent communication configuration."""

from __future__ import annotations

from pydantic import BaseModel


class CommsConfig(BaseModel):
    """Per-agent comms toggle.

    When enabled, the agent gains access to COMMS_TOOLS (send_email,
    send_discord, lookup_contact). Connection details (API keys, domain)
    live at the org level in OrgCommsConfig.
    """

    enabled: bool = False
    email_alias: str = ""  # e.g. "cipher" → cipher@{domain} instead of agent_id@{domain}

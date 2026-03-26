"""Per-agent integration configuration."""

from __future__ import annotations

from pydantic import BaseModel


class IntegrationConfig(BaseModel):
    """Per-agent integration toggle.

    Lists which external integrations this agent has access to.
    Each integration name corresponds to a module in axon.integrations.
    """

    enabled: list[str] = []  # e.g., ["google_calendar", "linear"]

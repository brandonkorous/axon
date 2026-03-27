"""Per-agent plugin configuration."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PluginsConfig(BaseModel):
    """Per-agent plugin toggle.

    Lists which plugins this agent has access to.
    Includes both tool plugins and integration plugins.
    """

    enabled: list[str] = Field(
        default_factory=list,
        description="Plugin names enabled for this agent",
    )

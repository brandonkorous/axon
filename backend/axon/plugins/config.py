"""Per-agent plugin configuration."""

from __future__ import annotations

from typing import Any

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
    config: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Per-plugin configuration: {plugin_name: {key: value}}",
    )

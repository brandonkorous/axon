"""Plugin instance configuration — org-level named environments."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PluginInstanceConfig(BaseModel):
    """A named, configured instance of a plugin shared across agents.

    Stored in org.yaml under ``plugin_instances``.
    """

    id: str  # unique slug, e.g. "axon-repo"
    plugin: str  # registry name, e.g. "sandbox"
    name: str = ""  # display name
    agents: list[str] = Field(default_factory=list)  # agent IDs with access
    config: dict[str, Any] = Field(default_factory=dict)  # plugin-specific kwargs

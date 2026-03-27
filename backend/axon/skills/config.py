"""Per-agent cognitive skills configuration."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SkillsConfig(BaseModel):
    """Per-agent skill toggle.

    Lists which cognitive skills this agent has enabled.
    """

    enabled: list[str] = Field(
        default_factory=list,
        description="Cognitive skill names enabled for this agent",
    )

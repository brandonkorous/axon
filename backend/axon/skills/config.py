"""Skills configuration — per-agent skill enablement."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SkillsConfig(BaseModel):
    """Per-agent skill configuration."""

    enabled: list[str] = Field(
        default_factory=list,
        description="Skill names enabled for this agent",
    )

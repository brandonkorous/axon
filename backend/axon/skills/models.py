"""Pydantic model for cognitive skill metadata loaded from skill.yaml."""

from __future__ import annotations

from pydantic import BaseModel


class SkillDefinition(BaseModel):
    """Metadata for a cognitive skill — loaded from skill.yaml."""

    name: str  # unique identifier, snake_case
    version: str = "1.0.0"
    description: str = ""
    author: str = "axon"
    category: str = "general"  # research, analysis, engineering, communication, planning
    icon: str = ""
    triggers: list[str] = []  # keywords that suggest this skill
    auto_inject: bool = False  # always inject when enabled

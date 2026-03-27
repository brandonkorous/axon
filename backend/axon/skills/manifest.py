"""Skill manifest — metadata and configuration for a skill package."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SkillManifest(BaseModel):
    """Declarative metadata for a skill package.

    Loaded from skill.yaml in the skill directory or declared
    programmatically by built-in skills.
    """

    name: str = Field(description="Unique skill identifier (snake_case)")
    version: str = Field(default="1.0.0", description="Semantic version")
    description: str = Field(default="", description="Human-readable description")
    author: str = Field(default="axon", description="Skill author or package name")

    # Tool configuration
    tool_prefix: str = Field(default="", description="Prefix for tool names (e.g. 'web_')")
    tools: list[str] = Field(default_factory=list, description="Tool names provided by this skill")

    # Dependencies
    python_deps: list[str] = Field(default_factory=list, description="Required Python packages")
    npm_deps: list[str] = Field(default_factory=list, description="Required npm packages (for sandbox)")

    # Credentials
    required_credentials: list[str] = Field(
        default_factory=list,
        description="Credential keys required (e.g. 'google_oauth', 'brave_api_key')",
    )

    # Loading behavior
    auto_load: bool = Field(
        default=False,
        description="Always load for agents with this skill enabled",
    )
    triggers: list[str] = Field(
        default_factory=list,
        description="Keywords/phrases that activate this skill on demand",
    )

    # Categorization
    category: str = Field(default="general", description="Skill category for UI grouping")
    icon: str = Field(default="", description="Icon name or emoji for UI display")

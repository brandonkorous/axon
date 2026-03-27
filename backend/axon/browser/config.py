"""Browser configuration — timeouts, allowlists, session limits."""

from __future__ import annotations

from pydantic import BaseModel, Field


class BrowserConfig(BaseModel):
    """Configuration for agent browser capabilities."""

    enabled: bool = Field(default=False, description="Enable browser tools for this agent")
    timeout_seconds: int = Field(default=30, description="Page load timeout")
    max_sessions: int = Field(default=3, description="Max concurrent browser sessions")
    max_content_length: int = Field(default=8000, description="Max extracted content chars")
    allow_domains: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Allowed domains (* = all)",
    )
    block_domains: list[str] = Field(
        default_factory=list,
        description="Blocked domains",
    )
    screenshot_enabled: bool = Field(default=True, description="Allow screenshots")

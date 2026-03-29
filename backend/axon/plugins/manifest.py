"""Plugin manifest — metadata and configuration for a plugin package."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PluginManifest(BaseModel):
    """Declarative metadata for a plugin package.

    Loaded from plugin.yaml in the plugin directory or declared
    programmatically by built-in plugins.
    """

    name: str = Field(description="Unique plugin identifier (snake_case)")
    version: str = Field(default="1.0.0", description="Semantic version")
    description: str = Field(default="", description="Human-readable description")
    author: str = Field(default="axon", description="Plugin author or package name")

    # Tool configuration
    tool_prefix: str = Field(default="", description="Prefix for tool names (e.g. 'web_')")
    tools: list[str] = Field(default_factory=list, description="Tool names provided by this plugin")

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
        description="Always load for agents with this plugin enabled",
    )
    triggers: list[str] = Field(
        default_factory=list,
        description="Keywords/phrases that activate this plugin on demand",
    )

    # Sandbox
    sandbox_type: str = Field(default="", description="Required sandbox type (base, code, browser, etc.)")

    # Categorization
    category: str = Field(default="general", description="Plugin category for UI grouping")
    icon: str = Field(default="", description="Icon name or emoji for UI display")

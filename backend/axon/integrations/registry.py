"""Integration registry — discover and load integration modules."""

from __future__ import annotations

from typing import Any

from axon.integrations.base import BaseIntegration

# Global registry of available integrations (name → class)
INTEGRATION_REGISTRY: dict[str, type[BaseIntegration]] = {}


def register_integration(name: str, cls: type[BaseIntegration]) -> None:
    """Register an integration class by name."""
    INTEGRATION_REGISTRY[name] = cls


def get_integration(name: str) -> type[BaseIntegration] | None:
    """Look up a registered integration by name."""
    return INTEGRATION_REGISTRY.get(name)


def get_tools_for_integrations(names: list[str]) -> list[dict[str, Any]]:
    """Collect tool schemas from all named integrations."""
    tools: list[dict[str, Any]] = []
    for name in names:
        cls = INTEGRATION_REGISTRY.get(name)
        if cls:
            instance = cls()
            tools.extend(instance.get_tools())
    return tools

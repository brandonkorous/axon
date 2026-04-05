"""Integration registry — discover and load integration modules."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

from axon.integrations.base import BaseIntegration
from axon.logging import get_logger

logger = get_logger(__name__)

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


def discover_integrations() -> None:
    """Import all integration subpackages to trigger registration."""
    integrations_dir = Path(__file__).parent
    for child in sorted(integrations_dir.iterdir()):
        if child.is_dir() and (child / "__init__.py").exists() and child.name != "__pycache__":
            try:
                importlib.import_module(f"axon.integrations.{child.name}")
                logger.debug("Discovered integration: %s", child.name)
            except Exception as e:
                logger.warning("Failed to load integration %s: %s", child.name, e)


def create_integration_executor(
    names: list[str],
    credentials_map: dict[str, dict[str, Any]] | None = None,
) -> "IntegrationToolExecutor | None":
    """Create an executor for the given integration names.

    Returns None if no valid integrations are found.
    """
    from axon.integrations.executor import IntegrationToolExecutor

    if not names:
        return None

    integrations: list[BaseIntegration] = []
    for name in names:
        cls = INTEGRATION_REGISTRY.get(name)
        if cls:
            instance = cls()
            instance.configure((credentials_map or {}).get(name))
            integrations.append(instance)
        else:
            logger.warning("Integration not found in registry: %s", name)

    return IntegrationToolExecutor(integrations) if integrations else None

"""Cognitive skills registry — global in-memory store of loaded skills."""

from __future__ import annotations

import logging
from pathlib import Path

from axon.skills.models import SkillDefinition

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Global registries
# ---------------------------------------------------------------------------

SKILL_REGISTRY: dict[str, SkillDefinition] = {}  # name → definition
SKILL_METHODOLOGY: dict[str, str] = {}  # name → methodology markdown content
SKILL_SOURCE: dict[str, str] = {}  # name → "builtin" or "external"


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register_skill(
    name: str,
    definition: SkillDefinition,
    methodology: str,
    source: str = "builtin",
) -> None:
    """Register a cognitive skill in the global registry."""
    SKILL_REGISTRY[name] = definition
    SKILL_METHODOLOGY[name] = methodology
    SKILL_SOURCE[name] = source
    logger.debug("Registered skill: %s (source=%s)", name, source)


def unregister_skill(name: str) -> None:
    """Remove a skill from all registries."""
    SKILL_REGISTRY.pop(name, None)
    SKILL_METHODOLOGY.pop(name, None)
    SKILL_SOURCE.pop(name, None)
    logger.debug("Unregistered skill: %s", name)


# ---------------------------------------------------------------------------
# Lookup
# ---------------------------------------------------------------------------

def get_skill(name: str) -> SkillDefinition | None:
    """Get a skill definition by name."""
    return SKILL_REGISTRY.get(name)


def get_methodology(name: str) -> str | None:
    """Get the methodology markdown for a skill."""
    return SKILL_METHODOLOGY.get(name)


def list_skills() -> list[dict]:
    """Return metadata for all registered skills."""
    results = []
    for name, defn in SKILL_REGISTRY.items():
        methodology = SKILL_METHODOLOGY.get(name, "")
        results.append({
            "name": defn.name,
            "description": defn.description,
            "version": defn.version,
            "author": defn.author,
            "category": defn.category,
            "icon": defn.icon,
            "triggers": defn.triggers,
            "auto_inject": defn.auto_inject,
            "is_builtin": SKILL_SOURCE.get(name, "builtin") == "builtin",
            "source": SKILL_SOURCE.get(name, "builtin"),
            "methodology_preview": methodology[:200],
        })
    return results


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def discover_skills() -> None:
    """Scan backend/axon/skills/builtin/ for subdirs with skill.yaml + methodology.md."""
    from axon.skills.loader import load_skill_from_directory

    builtin_dir = Path(__file__).parent / "builtin"
    if not builtin_dir.exists():
        logger.debug("No builtin skills directory found at %s", builtin_dir)
        return

    count = 0
    for child in sorted(builtin_dir.iterdir()):
        if not child.is_dir() or child.name.startswith("_"):
            continue
        if (child / "skill.yaml").exists():
            if load_skill_from_directory(child):
                count += 1

    logger.info("Discovered %d built-in cognitive skill(s)", count)

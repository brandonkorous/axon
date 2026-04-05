"""Pattern registry — discovers and loads cognitive pattern libraries."""

from __future__ import annotations

from pathlib import Path

import yaml

from axon.logging import get_logger
from axon.patterns.models import CognitivePattern

logger = get_logger(__name__)

# Global registries
PATTERN_REGISTRY: dict[str, CognitivePattern] = {}  # name -> definition
PATTERN_METHODOLOGY: dict[str, str] = {}  # name -> methodology markdown


def discover_patterns() -> None:
    """Discover and register all built-in cognitive patterns."""
    library_dir = Path(__file__).parent / "library"
    if not library_dir.exists():
        return

    count = 0
    for role_dir in sorted(library_dir.iterdir()):
        if not role_dir.is_dir():
            continue
        for pattern_dir in sorted(role_dir.iterdir()):
            if not pattern_dir.is_dir():
                continue
            yaml_path = pattern_dir / "pattern.yaml"
            md_path = pattern_dir / "methodology.md"
            if not yaml_path.exists() or not md_path.exists():
                continue
            try:
                with open(yaml_path, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if not data or "name" not in data:
                    continue
                defn = CognitivePattern(**data)
                methodology = md_path.read_text(encoding="utf-8").strip()
                PATTERN_REGISTRY[defn.name] = defn
                PATTERN_METHODOLOGY[defn.name] = methodology
                count += 1
            except Exception:
                logger.exception("Failed to load pattern from %s", pattern_dir)

    logger.info("Discovered %d cognitive pattern(s)", count)


def get_patterns_for_role(role: str) -> list[CognitivePattern]:
    """Get all patterns matching a given role."""
    role_lower = role.lower()
    return [
        p for p in PATTERN_REGISTRY.values()
        if role_lower in [r.lower() for r in p.roles]
    ]


def list_patterns() -> list[dict]:
    """List all patterns with metadata (for API/UI)."""
    return [
        {
            "name": p.name,
            "display_name": p.display_name,
            "attribution": p.attribution,
            "roles": p.roles,
            "description": p.description,
        }
        for p in PATTERN_REGISTRY.values()
    ]

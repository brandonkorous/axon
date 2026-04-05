"""Cognitive skill loader — reads skill.yaml + methodology.md from disk."""

from __future__ import annotations

from pathlib import Path

import yaml

from axon.logging import get_logger
from axon.skills.models import SkillDefinition
from axon.skills.registry import register_skill

logger = get_logger(__name__)


def load_skill_from_directory(skill_dir: Path, source: str = "builtin") -> bool:
    """Load a cognitive skill from a directory containing skill.yaml + methodology.md.

    Returns True if loaded successfully, False otherwise.
    """
    yaml_path = skill_dir / "skill.yaml"
    md_path = skill_dir / "methodology.md"

    if not yaml_path.exists():
        logger.warning("No skill.yaml found in %s", skill_dir)
        return False

    try:
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception:
        logger.exception("Failed to parse skill.yaml in %s", skill_dir)
        return False

    # Use directory name as skill name if not specified
    if "name" not in data:
        data["name"] = skill_dir.name

    try:
        definition = SkillDefinition(**data)
    except Exception:
        logger.exception("Invalid skill definition in %s", skill_dir)
        return False

    # Load methodology markdown (optional but expected)
    methodology = ""
    if md_path.exists():
        try:
            methodology = md_path.read_text(encoding="utf-8")
        except Exception:
            logger.exception("Failed to read methodology.md in %s", skill_dir)

    register_skill(definition.name, definition, methodology, source=source)
    return True


def load_org_skills(orgs_dir: str, org_id: str) -> list[str]:
    """Scan orgs/{org_id}/skills/ for custom cognitive skills.

    Returns list of skill names that were loaded.
    """
    skills_dir = Path(orgs_dir) / org_id / "skills"
    if not skills_dir.exists():
        return []

    loaded: list[str] = []
    for child in sorted(skills_dir.iterdir()):
        if not child.is_dir() or child.name.startswith("_"):
            continue
        if (child / "skill.yaml").exists():
            if load_skill_from_directory(child, source="external"):
                loaded.append(child.name)

    if loaded:
        logger.info("Loaded %d org skill(s) for %s: %s", len(loaded), org_id, loaded)
    return loaded

"""Skill loader — dynamic import and validation of skill packages."""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import Any

import yaml

from axon.skills.base import BaseSkill
from axon.skills.manifest import SkillManifest
from axon.skills.registry import register_skill

logger = logging.getLogger(__name__)


def load_skill_from_directory(skill_dir: Path) -> type[BaseSkill] | None:
    """Load a skill from a directory containing skill.yaml and __init__.py.

    Returns the skill class if successful, None otherwise.
    """
    manifest_path = skill_dir / "skill.yaml"
    init_path = skill_dir / "__init__.py"

    if not manifest_path.exists():
        logger.warning("No skill.yaml in %s", skill_dir)
        return None
    if not init_path.exists():
        logger.warning("No __init__.py in %s", skill_dir)
        return None

    # Load and validate manifest
    manifest = _load_manifest(manifest_path)
    if not manifest:
        return None

    # Import the module
    try:
        module_name = f"axon_skill_{manifest.name}"
        spec = importlib.util.spec_from_file_location(module_name, init_path)
        if not spec or not spec.loader:
            logger.warning("Failed to create module spec for %s", skill_dir)
            return None

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Look for the skill class (must extend BaseSkill)
        skill_cls = _find_skill_class(module)
        if not skill_cls:
            logger.warning("No BaseSkill subclass found in %s", skill_dir)
            return None

        # Inject manifest if not already set
        if not hasattr(skill_cls, "manifest") or skill_cls.manifest is None:
            skill_cls.manifest = manifest

        register_skill(manifest.name, skill_cls)
        logger.info("Loaded external skill: %s v%s", manifest.name, manifest.version)
        return skill_cls

    except Exception as e:
        logger.exception("Failed to load skill from %s: %s", skill_dir, e)
        return None


def load_org_skills(orgs_dir: str, org_id: str) -> list[str]:
    """Discover and load skills from an org's skills directory.

    Returns list of loaded skill names.
    """
    skills_dir = Path(orgs_dir) / org_id / "skills"
    if not skills_dir.is_dir():
        return []

    loaded: list[str] = []
    for child in sorted(skills_dir.iterdir()):
        if child.is_dir() and (child / "skill.yaml").exists():
            cls = load_skill_from_directory(child)
            if cls:
                loaded.append(cls().manifest.name)

    return loaded


def _load_manifest(path: Path) -> SkillManifest | None:
    """Parse and validate a skill.yaml manifest file."""
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return SkillManifest(**data)
    except Exception as e:
        logger.warning("Invalid skill manifest %s: %s", path, e)
        return None


def _find_skill_class(module: Any) -> type[BaseSkill] | None:
    """Find the first BaseSkill subclass in a module."""
    for name in dir(module):
        obj = getattr(module, name)
        if (
            isinstance(obj, type)
            and issubclass(obj, BaseSkill)
            and obj is not BaseSkill
        ):
            return obj
    return None

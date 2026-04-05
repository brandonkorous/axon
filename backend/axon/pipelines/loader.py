"""Pipeline loader -- discovers and loads pipeline YAML definitions."""

from __future__ import annotations

from pathlib import Path

import yaml

from axon.logging import get_logger
from axon.pipelines.models import PipelineDefinition

logger = get_logger(__name__)

# Global registry of loaded pipeline definitions
PIPELINE_REGISTRY: dict[str, dict[str, PipelineDefinition]] = {}


def load_org_pipelines(
    org_dir: str | Path, org_id: str,
) -> dict[str, PipelineDefinition]:
    """Load pipeline definitions for an organization.

    Searches:
    1. {org_dir}/pipelines/*.yaml
    2. {org_dir}/vaults/shared/pipelines/*.yaml
    """
    pipelines: dict[str, PipelineDefinition] = {}
    org_path = Path(org_dir)

    search_dirs = [
        org_path / "pipelines",
        org_path / "vaults" / "shared" / "pipelines",
    ]

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for yaml_file in sorted(search_dir.glob("*.yaml")):
            try:
                with open(yaml_file, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if not data or "name" not in data:
                    continue
                defn = PipelineDefinition(**data)
                pipelines[defn.name] = defn
                logger.debug(
                    "[%s] Loaded pipeline '%s' from %s (%d steps)",
                    org_id, defn.name, yaml_file.name, len(defn.steps),
                )
            except Exception:
                logger.exception(
                    "Failed to load pipeline from %s", yaml_file,
                )

    PIPELINE_REGISTRY[org_id] = pipelines
    return pipelines


def get_pipeline(
    org_id: str, name: str,
) -> PipelineDefinition | None:
    """Get a pipeline definition by org and name."""
    return PIPELINE_REGISTRY.get(org_id, {}).get(name)


def list_pipelines(org_id: str) -> list[PipelineDefinition]:
    """List all pipeline definitions for an org."""
    return list(PIPELINE_REGISTRY.get(org_id, {}).values())

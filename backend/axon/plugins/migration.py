"""Migrate per-agent plugin configs to org-level plugin instances."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import yaml

from axon.plugins.instance import PluginInstanceConfig

logger = logging.getLogger(__name__)

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slugify(text: str) -> str:
    return _SLUG_RE.sub("-", text.lower()).strip("-")


def migrate_plugin_configs(
    org_dir: Path,
    agent_registry: dict[str, Any],
) -> list[PluginInstanceConfig]:
    """Scan agents for legacy plugin configs and produce instance configs.

    Returns a list of PluginInstanceConfig entries. Does NOT write to disk.
    Caller is responsible for persisting to org.yaml.
    """
    # Collect (plugin_name, config_dict, agent_id) triples
    raw: list[tuple[str, dict[str, Any], str]] = []
    for agent_id, agent in agent_registry.items():
        plugins_cfg = getattr(agent, "config", None)
        if plugins_cfg is None:
            continue
        plugins = getattr(plugins_cfg, "plugins", None)
        if plugins is None or not plugins.enabled:
            continue
        for plugin_name in plugins.enabled:
            cfg = (plugins.config or {}).get(plugin_name, {})
            raw.append((plugin_name, cfg, agent_id))

    if not raw:
        return []

    # Group by (plugin_name, config_fingerprint) to deduplicate
    groups: dict[str, tuple[str, dict[str, Any], list[str]]] = {}
    for plugin_name, cfg, agent_id in raw:
        # Fingerprint: plugin + path + sorted executables
        fp_parts = [
            plugin_name,
            str(cfg.get("path", "") or ""),
            ",".join(sorted(cfg.get("executables", []))),
            str(cfg.get("host_agent_id", "") or ""),
        ]
        fp = "|".join(fp_parts)
        if fp in groups:
            groups[fp][2].append(agent_id)
        else:
            groups[fp] = (plugin_name, cfg, [agent_id])

    instances: list[PluginInstanceConfig] = []
    counters: dict[str, int] = {}

    for plugin_name, cfg, agents in groups.values():
        # Generate a readable ID
        path = cfg.get("path", "")
        if path:
            name_hint = Path(path).name or plugin_name
        else:
            name_hint = "scratch" if plugin_name == "sandbox" else plugin_name
        slug = _slugify(name_hint)
        # Ensure unique
        counters.setdefault(slug, 0)
        if counters[slug] > 0:
            slug = f"{slug}-{counters[slug]}"
        counters[slug] = counters.get(slug, 0) + 1

        # Clean config: drop null values
        clean_cfg = {k: v for k, v in cfg.items() if v is not None}

        display_name = name_hint.replace("-", " ").replace("_", " ").title()
        instances.append(PluginInstanceConfig(
            id=slug,
            plugin=plugin_name,
            name=display_name,
            agents=agents,
            config=clean_cfg,
        ))

    logger.info(
        "Migrated %d agent plugin configs → %d instances",
        len(raw), len(instances),
    )
    return instances


def persist_instances_to_org(
    org_dir: Path,
    instances: list[PluginInstanceConfig],
) -> None:
    """Write plugin_instances to org.yaml."""
    yaml_path = org_dir / "org.yaml"
    data: dict[str, Any] = {}
    if yaml_path.exists():
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

    data["plugin_instances"] = [inst.model_dump() for inst in instances]

    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    logger.info("Wrote %d plugin instances to %s", len(instances), yaml_path)

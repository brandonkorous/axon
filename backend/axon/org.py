"""Organization management — multi-org support for Axon."""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml
from enum import Enum
from pydantic import BaseModel

logger = logging.getLogger(__name__)

from axon.vault.scaffold import scaffold_vault

if TYPE_CHECKING:
    from axon.agents.agent import Agent
    from axon.agents.huddle import Huddle
    from axon.audit import AuditLogger
    from axon.usage import UsageTracker
    from axon.vault.vault import VaultManager


class OrgType(str, Enum):
    """Built-in organization types with curated persona sets."""

    FAMILY = "family"
    STARTUP = "startup"
    JOB_HUNT = "job-hunt"
    CREATOR = "creator"
    STUDENT = "student"
    CUSTOM = "custom"


class DiscordConfig(BaseModel):
    """Discord integration settings for an organization."""

    bot_token_env: str = ""  # env var name holding the token
    guild_id: str = ""
    channel_mappings: dict[str, str] = {}  # channel_id -> agent_id


class OrgConfig(BaseModel):
    """Organization configuration, loaded from org.yaml."""

    id: str
    name: str
    description: str = ""
    type: OrgType = OrgType.CUSTOM
    settings_overrides: dict[str, Any] = {}
    discord: DiscordConfig | None = None


@dataclass
class OrgInstance:
    """A fully initialized organization with its agents and vaults."""

    config: OrgConfig
    agent_registry: dict[str, "Agent"] = field(default_factory=dict)
    huddle: "Huddle | None" = None
    shared_vault: "VaultManager | None" = None
    audit_logger: "AuditLogger | None" = None
    usage_tracker: "UsageTracker | None" = None

    @property
    def id(self) -> str:
        return self.config.id

    @property
    def name(self) -> str:
        return self.config.name


# ── Loading ─────────────────────────────────────────────────────────


def load_org_config(org_dir: str | Path) -> OrgConfig:
    """Load an organization config from its directory's org.yaml."""
    org_path = Path(org_dir)
    yaml_path = org_path / "org.yaml"

    if not yaml_path.exists():
        # Generate a default config from the directory name
        return OrgConfig(
            id=org_path.name,
            name=org_path.name.replace("-", " ").title(),
        )

    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    # Ensure id matches directory name
    data.setdefault("id", org_path.name)
    data.setdefault("name", org_path.name.replace("-", " ").title())
    return OrgConfig(**data)


def discover_orgs(orgs_dir: str | Path) -> list[Path]:
    """Discover all organization directories under the orgs root."""
    orgs_path = Path(orgs_dir)
    if not orgs_path.exists():
        return []
    return sorted(
        d for d in orgs_path.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    )


# ── Scaffolding ─────────────────────────────────────────────────────


SHARED_VAULT_TEMPLATE_DIR = Path(__file__).parent / "vault_templates" / "shared"


def scaffold_org(
    org_dir: str | Path,
    org_name: str = "",
    org_description: str = "",
) -> Path:
    """Scaffold a new organization directory with shared vault.

    Creates:
      org_dir/
        org.yaml
        personas/
          prompts/
        vaults/
          shared/
            second-brain.md
            tasks/tasks-index.md
            issues/issues-index.md
            achievements/achievements-index.md
            decisions/decisions-log.md
        data/
          conversations/
          agent-state/
    """
    org_path = Path(org_dir)
    org_id = org_path.name

    if not org_name:
        org_name = org_id.replace("-", " ").title()

    # Create directory structure
    (org_path / "vaults").mkdir(parents=True, exist_ok=True)
    (org_path / "data" / "conversations").mkdir(parents=True, exist_ok=True)
    (org_path / "data" / "agent-state").mkdir(parents=True, exist_ok=True)
    (org_path / "runners").mkdir(parents=True, exist_ok=True)

    # Write org.yaml
    org_config = {
        "id": org_id,
        "name": org_name,
        "description": org_description,
    }
    yaml_path = org_path / "org.yaml"
    if not yaml_path.exists():
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(org_config, f, default_flow_style=False, sort_keys=False)

    # Scaffold shared vault from template
    shared_vault_path = org_path / "vaults" / "shared"
    if not shared_vault_path.exists() or not any(shared_vault_path.iterdir() if shared_vault_path.exists() else []):
        _scaffold_shared_vault(shared_vault_path, org_name)

    return org_path


def _scaffold_shared_vault(vault_path: Path, org_name: str) -> None:
    """Initialize the shared vault from template or built-in defaults."""
    vault_path.mkdir(parents=True, exist_ok=True)

    if SHARED_VAULT_TEMPLATE_DIR.exists():
        # Copy from template
        for item in SHARED_VAULT_TEMPLATE_DIR.rglob("*"):
            relative = item.relative_to(SHARED_VAULT_TEMPLATE_DIR)
            target = vault_path / relative
            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                content = item.read_text(encoding="utf-8")
                content = content.replace("{{ORG_NAME}}", org_name)
                target.write_text(content, encoding="utf-8")
    else:
        # Built-in defaults if no template directory exists
        _write_default_shared_vault(vault_path, org_name)


def _write_default_shared_vault(vault_path: Path, org_name: str) -> None:
    """Write default shared vault files when no template exists."""
    # Root
    (vault_path / "second-brain.md").write_text(
        f"# {org_name} — Shared Vault\n\n"
        "Shared knowledge base for the organization. All agents can read; "
        "write access is configurable per agent.\n\n"
        "## Branches\n\n"
        "### Tasks\nActive work items and assignments.\n- [[tasks/tasks-index]]\n\n"
        "### Issues\nBugs, problems, and improvement requests.\n- [[issues/issues-index]]\n\n"
        "### Achievements\nMilestones and outcomes worth celebrating.\n- [[achievements/achievements-index]]\n\n"
        "### Decisions\nStrategic decisions with reasoning.\n- [[decisions/decisions-log]]\n",
        encoding="utf-8",
    )

    # Tasks
    tasks_dir = vault_path / "tasks"
    tasks_dir.mkdir(exist_ok=True)
    (tasks_dir / "tasks-index.md").write_text(
        "---\nname: Tasks Index\ndescription: Active tasks and assignments\ntype: index\n---\n\n"
        "# Tasks\n\nAll tasks, newest first.\n",
        encoding="utf-8",
    )

    # Issues
    issues_dir = vault_path / "issues"
    issues_dir.mkdir(exist_ok=True)
    (issues_dir / "issues-index.md").write_text(
        "---\nname: Issues Index\ndescription: Bugs, problems, and improvement requests\ntype: index\n---\n\n"
        "# Issues\n\nAll issues, newest first.\n",
        encoding="utf-8",
    )
    (issues_dir / ".next_id").write_text("1", encoding="utf-8")

    # Achievements
    achievements_dir = vault_path / "achievements"
    achievements_dir.mkdir(exist_ok=True)
    (achievements_dir / "achievements-index.md").write_text(
        "---\nname: Achievements Index\ndescription: Milestones and outcomes\ntype: index\n---\n\n"
        "# Achievements\n\nMilestones worth celebrating.\n",
        encoding="utf-8",
    )

    # Decisions
    decisions_dir = vault_path / "decisions"
    decisions_dir.mkdir(exist_ok=True)
    (decisions_dir / "decisions-log.md").write_text(
        "---\nname: Decisions Log\ndescription: Strategic decisions with reasoning\ntype: index\n---\n\n"
        "# Decisions\n\nAll strategic decisions, newest first.\n",
        encoding="utf-8",
    )

    # Audit (empty — append-only, will be populated by AuditLogger)
    (vault_path / "audit").mkdir(exist_ok=True)


# ── Migration ───────────────────────────────────────────────────────


def migrate_to_multi_org(
    personas_dir: str | Path,
    vaults_dir: str | Path,
    data_dir: str | Path,
    orgs_dir: str | Path,
) -> Path:
    """Migrate a single-org Axon installation to multi-org layout.

    Moves existing personas, vaults, and data into orgs/default/.
    Returns the path to the default org.

    Only runs if orgs_dir is empty or doesn't exist, AND the old flat
    layout (personas_dir) has content.
    """
    orgs_path = Path(orgs_dir)
    personas_path = Path(personas_dir)
    vaults_path = Path(vaults_dir)
    data_path = Path(data_dir)

    # Don't migrate if orgs already has content
    if orgs_path.exists() and any(orgs_path.iterdir()):
        return orgs_path

    # Don't migrate if there's nothing to migrate
    if not personas_path.exists() or not any(personas_path.glob("*.yaml")):
        return orgs_path

    print("[AXON] Migrating single-org layout to multi-org...")

    default_org = orgs_path / "default"
    scaffold_org(default_org, org_name="Default Organization")

    # Move personas
    dest_personas = default_org / "personas"
    for item in personas_path.iterdir():
        dest = dest_personas / item.name
        if not dest.exists():
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

    # Move vaults (symlink or copy)
    dest_vaults = default_org / "vaults"
    if vaults_path.exists():
        for vault_dir in vaults_path.iterdir():
            if vault_dir.is_dir() and vault_dir.name != "shared":
                dest = dest_vaults / vault_dir.name
                if not dest.exists():
                    shutil.copytree(vault_dir, dest)

    # Move conversation data
    conversations_src = data_path / "conversations"
    conversations_dest = default_org / "data" / "conversations"
    if conversations_src.exists():
        for item in conversations_src.iterdir():
            dest = conversations_dest / item.name
            if not dest.exists():
                shutil.copy2(item, dest)

    print(f"[AXON] Migration complete → {default_org}")
    return orgs_path


# ── Agent-as-Vault Migration ──────────────────────────────────────


# Heuristics for inferring agent type from legacy persona config
_TYPE_HEURISTICS = {
    "axon": "orchestrator",
    "huddle": "huddle",
}


def migrate_personas_to_vaults(org_dir: str | Path) -> list[str]:
    """Migrate legacy personas/*.yaml into vault-based agent.yaml files.

    For each persona YAML:
    1. Resolves the vault directory from vault.path
    2. Writes agent.yaml into the vault directory
    3. Copies {id}_instructions.md into the vault as instructions.md
    4. Renames personas/ to personas.bak/

    Returns list of migrated agent IDs.
    """
    org_path = Path(org_dir)
    personas_dir = org_path / "personas"
    vaults_dir = org_path / "vaults"

    if not personas_dir.exists():
        logger.warning("No personas/ directory found in %s", org_path)
        return []

    migrated: list[str] = []

    for yaml_file in sorted(personas_dir.glob("*.yaml")):
        if yaml_file.name.startswith("_"):
            continue

        with open(yaml_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or "id" not in data:
            continue

        agent_id = data["id"]
        vault_spec = data.get("vault", {}).get("path", f"/vaults/{agent_id}")

        # Resolve vault directory
        parts = vault_spec.replace("\\", "/").strip("/").split("/")
        if len(parts) >= 2 and parts[0] == "vaults":
            vault_name = parts[1]
        else:
            vault_name = agent_id
        vault_dir = vaults_dir / vault_name

        if not vault_dir.exists():
            vault_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Created vault directory: %s", vault_dir)

        # Build agent.yaml data (strip vault.path, add type)
        agent_data = dict(data)

        # Remove vault.path (implicit in agent-as-vault)
        if "vault" in agent_data:
            agent_data["vault"].pop("path", None)
            # Convert writable_paths to relative
            wp = agent_data["vault"].get("writable_paths", [])
            agent_data["vault"]["writable_paths"] = [
                "." if p == vault_spec else p for p in wp
            ]

        # Infer type from ID or external flag
        if "type" not in agent_data:
            if agent_data.get("external", False):
                agent_data["type"] = "external"
            elif agent_id in _TYPE_HEURISTICS:
                agent_data["type"] = _TYPE_HEURISTICS[agent_id]
            else:
                agent_data["type"] = "advisor"

        # Remove legacy fields
        agent_data.pop("system_prompt_file", None)

        # Write agent.yaml
        agent_yaml_path = vault_dir / "agent.yaml"
        with open(agent_yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(agent_data, f, default_flow_style=False, sort_keys=False)

        # Copy instructions file
        instructions_src = None
        # Try {id}_instructions.md first
        candidate = personas_dir / f"{agent_id}_instructions.md"
        if candidate.exists():
            instructions_src = candidate
        else:
            # Try prompts/{id}_instructions.md
            candidate = personas_dir / "prompts" / f"{agent_id}_instructions.md"
            if candidate.exists():
                instructions_src = candidate
            else:
                # Try the system_prompt_file field
                spf = data.get("system_prompt_file", "")
                if spf:
                    candidate = personas_dir / spf
                    if candidate.exists():
                        instructions_src = candidate

        if instructions_src:
            dest = vault_dir / "instructions.md"
            if not dest.exists():
                shutil.copy2(instructions_src, dest)
                logger.info("Copied %s → %s", instructions_src.name, dest)

        migrated.append(agent_id)
        logger.info("Migrated agent '%s' → %s/agent.yaml", agent_id, vault_dir)

    # Rename personas/ to personas.bak/
    if migrated:
        backup = org_path / "personas.bak"
        if backup.exists():
            shutil.rmtree(backup)
        personas_dir.rename(backup)
        logger.info("Renamed personas/ → personas.bak/")

    return migrated

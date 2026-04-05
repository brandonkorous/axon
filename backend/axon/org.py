"""Organization management — multi-org support for Axon."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml
from enum import Enum
from pydantic import BaseModel, Field

from axon.logging import get_logger
from axon.plugins.instance import PluginInstanceConfig

logger = get_logger(__name__)

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

    guild_id: str = ""
    channel_mappings: dict[str, str] = {}  # channel_id -> agent_id


class SlackConfig(BaseModel):
    """Slack integration settings for an organization."""

    channel_mappings: dict[str, str] = {}  # channel_id -> agent_id


class TeamsConfig(BaseModel):
    """Microsoft Teams integration settings for an organization."""

    tenant_id: str = ""  # Azure AD tenant ID
    channel_mappings: dict[str, str] = {}  # channel_id -> agent_id


class ZoomConfig(BaseModel):
    """Zoom integration settings for an organization."""

    channel_mappings: dict[str, str] = {}  # Zoom Team Chat channel_id -> agent_id


class RegisteredModel(BaseModel):
    """A model registered for use in this org."""

    id: str  # e.g. "anthropic/claude-sonnet-4-20250514"
    provider: str = ""  # "anthropic", "openai", "ollama"
    display_name: str = ""  # Human-friendly name
    model_type: str = "cloud"  # "cloud" or "local"


class ModelRoleAssignments(BaseModel):
    """Org-level default model for each role."""

    navigator: str = ""  # Tool routing, intent classification
    reasoning: str = ""  # Main agent conversation
    memory: str = ""  # Vault recall, memory consolidation
    agent: str = ""  # Default for agent conversations


class OrgModelConfig(BaseModel):
    """Org-level model management."""

    registered_models: list[RegisteredModel] = Field(default_factory=list)
    roles: ModelRoleAssignments = ModelRoleAssignments()
    api_keys: dict[str, str] = Field(default_factory=dict)  # provider → key


class HostAgentConfig(BaseModel):
    """A registered host agent service."""

    id: str  # Unique identifier, e.g. "dev-environment"
    name: str = ""  # Display name, e.g. "Dev Environment"
    path: str  # Root directory on the host
    port: int = 9100  # Port the host agent listens on
    host: str = "host.docker.internal"  # How the backend reaches the host
    executables: list[str] = Field(default_factory=list)
    status: str = "stopped"  # "running", "stopped", "unknown"


class OrgCommsConfig(BaseModel):
    """Organization-level communication settings."""

    require_approval: bool = True  # require user approval for outbound messages
    email_domain: str = ""  # e.g. "axon.yourcompany.com"
    email_signature: str = ""  # HTML appended to every outbound email
    inbound_polling: bool = False  # enable inbound email polling (requires Resend inbound support)
    discord: DiscordConfig | None = None  # unified discord config
    slack: SlackConfig | None = None  # Slack integration config
    teams: TeamsConfig | None = None  # Microsoft Teams integration config
    zoom: ZoomConfig | None = None  # Zoom integration config


class OrgConfig(BaseModel):
    """Organization configuration, loaded from org.yaml."""

    id: str
    name: str
    description: str = ""
    type: OrgType = OrgType.CUSTOM
    principles_file: str = "principles.md"  # path relative to shared vault
    settings_overrides: dict[str, Any] = {}
    discord: DiscordConfig | None = None  # legacy — use comms.discord instead
    comms: OrgCommsConfig = OrgCommsConfig()
    models: OrgModelConfig = OrgModelConfig()
    host_agents: list[HostAgentConfig] = Field(default_factory=list)
    plugin_instances: list[PluginInstanceConfig] = Field(default_factory=list)


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

    config = OrgConfig(**data)

    # Backward compat: merge legacy top-level discord into comms.discord
    if config.discord and not config.comms.discord:
        config.comms.discord = config.discord

    return config


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

    # Contacts
    contacts_dir = vault_path / "contacts"
    contacts_dir.mkdir(exist_ok=True)
    (contacts_dir / "contacts-index.md").write_text(
        "---\nname: Contacts Index\ndescription: Directory of contacts for agent communication\ntype: index\n---\n\n"
        "# Contacts\n\nOrganization contacts for agent communication.\n",
        encoding="utf-8",
    )

    # Audit (empty — append-only, will be populated by AuditLogger)
    (vault_path / "audit").mkdir(exist_ok=True)


# ── Huddle auto-creation ────────────────────────────────────────────


def ensure_huddle(org: "OrgInstance", orgs_dir: str | Path) -> bool:
    """Ensure the org has a huddle if it has advisors.

    Creates the huddle vault, config, and Huddle instance on-the-fly.
    Returns True if a huddle was created, False if one already existed
    or there are no advisors.
    """
    if org.huddle:
        return False

    from axon.config import AgentType, PersonaConfig, VaultConfig, _load_agent_yaml
    from axon.agents.huddle import Huddle

    # Collect advisor configs and agents
    advisor_configs: dict[str, PersonaConfig] = {}
    advisor_agents: dict[str, "Agent"] = {}
    for aid, agent in org.agent_registry.items():
        if hasattr(agent, "config") and agent.config.type == AgentType.ADVISOR:
            advisor_configs[aid] = agent.config
            advisor_agents[aid] = agent

    if not advisor_configs:
        return False

    org_dir = Path(orgs_dir) / org.config.id
    vaults_dir = org_dir / "vaults"
    data_dir = str(org_dir / "data")
    huddle_vault_path = vaults_dir / "huddle"

    # Scaffold huddle vault if it doesn't exist
    if not huddle_vault_path.exists() or not (huddle_vault_path / "agent.yaml").exists():
        huddle_vault_path.mkdir(parents=True, exist_ok=True)

        # Build read-only mounts for all advisors
        mounts = [
            {"path": str(vaults_dir / aid), "root_file": "second-brain.md"}
            for aid in advisor_configs
        ]

        huddle_config = {
            "id": "huddle",
            "name": "The Huddle",
            "title": "Advisory Group Session",
            "tagline": "Where your team debates, disagrees, and converges",
            "type": "huddle",
            "model": {"max_tokens": 8192, "temperature": 0.8},
            "voice": {"engine": "disabled", "voice_id": "", "speed": 1.0},
            "vault": {
                "root_file": "second-brain.md",
                "read_only_mounts": mounts,
                "writable_paths": [str(huddle_vault_path)],
            },
            "memory": {"max_context_tokens": 6000},
            "delegation": {"can_delegate_to": [], "accepts_from": ["axon"]},
            "behavior": {"auto_save": True, "first_message": True, "proactive_checks": []},
            "ui": {"color": "#F59E0B", "avatar": "", "sparkle_color": "#FBBF24"},
        }

        agent_yaml_path = huddle_vault_path / "agent.yaml"
        with open(agent_yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(huddle_config, f, default_flow_style=False, sort_keys=False)

        # Create a minimal second-brain.md
        root_file = huddle_vault_path / "second-brain.md"
        if not root_file.exists():
            root_file.write_text(
                "# The Huddle\n\nGroup advisory session memory.\n",
                encoding="utf-8",
            )

        # Write default instructions
        instructions_path = huddle_vault_path / "instructions.md"
        if not instructions_path.exists():
            roster = "\n".join(
                f"- **{cfg.name}** — {cfg.title}" for cfg in advisor_configs.values()
            )
            instructions_path.write_text(
                f"# The Huddle\n\n"
                f"You orchestrate a group advisory session. Each advisor speaks in character "
                f"with their own expertise and perspective.\n\n"
                f"## Advisors\n\n{roster}\n\n"
                f"## Rules\n\n"
                f"- Each advisor speaks in turn, using **Name:** prefix\n"
                f"- Advisors may disagree — that's the point\n"
                f"- End with a **Table:** synthesis summarizing consensus and open questions\n",
                encoding="utf-8",
            )

    # Load the config and create the Huddle instance
    agent_yaml_path = huddle_vault_path / "agent.yaml"
    config = _load_agent_yaml(agent_yaml_path, huddle_vault_path, org_model_config=org.config.models)

    org.huddle = Huddle(
        config,
        advisor_configs,
        data_dir=data_dir,
        usage_tracker=org.usage_tracker,
        shared_vault=org.shared_vault,
        org_id=org.config.id,
        advisor_agents=advisor_agents,
    )

    logger.info("Auto-created huddle for org '%s' with %d advisors", org.config.id, len(advisor_configs))
    return True

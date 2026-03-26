"""Axon configuration — loaded from environment and agent YAML files."""

from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings

from axon.comms.config import CommsConfig  # noqa: E402 — no circular import risk
from axon.integrations.config import IntegrationConfig  # noqa: E402
from axon.reasoning.config import ReasoningConfig  # noqa: E402 — no circular import risk (lazy __init__)
from axon.web.config import WebConfig  # noqa: E402

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Agent type — determines which class gets instantiated."""

    ADVISOR = "advisor"
    ORCHESTRATOR = "orchestrator"
    HUDDLE = "huddle"
    EXTERNAL = "external"


class Settings(BaseSettings):
    """Global settings from environment variables."""

    anthropic_api_key: str = ""
    openai_api_key: str = ""
    ollama_base_url: str = "http://ollama:11434"
    default_model: str = "anthropic/claude-sonnet-4-20250514"
    axon_orgs_dir: str = "./orgs"  # Multi-org root — all orgs, vaults, and data
    axon_log_level: str = "INFO"  # Logging level (DEBUG, INFO, WARNING, ERROR)
    database_url: str = ""  # Empty → auto-derive SQLite from axon_orgs_dir
    db_encryption_key: str = ""  # Fernet key for encrypting credentials at rest

    class Config:
        # Look for .env in project root (one level up from backend/)
        env_file = [
            str(Path(__file__).resolve().parent.parent.parent / ".env"),  # D:/corp/axon/.env
            "../.env",
            ".env",
        ]


class ModelConfig(BaseModel):
    """Per-agent model configuration.

    If reasoning/navigator are empty or omitted, they inherit from
    the DEFAULT_MODEL env var (defaults to claude-sonnet).
    """

    reasoning: str = ""
    navigator: str = ""
    max_tokens: int = 4096
    temperature: float = 0.7


class VoiceConfig(BaseModel):
    """Per-agent voice configuration."""

    engine: str = "disabled"  # piper | xtts | elevenlabs | disabled
    voice_id: str = ""
    speed: float = 1.0


class VaultMount(BaseModel):
    """A read-only vault mount for cross-agent access."""

    path: str
    root_file: str = "second-brain.md"


class VaultConfig(BaseModel):
    """Per-agent vault configuration."""

    path: str = ""  # Set automatically in agent-as-vault mode
    root_file: str = "second-brain.md"
    read_only_mounts: list[VaultMount] = []
    writable_paths: list[str] = []


class MemoryConfig(BaseModel):
    """Memory navigator configuration."""

    navigator_model: str | None = None  # defaults to agent's navigator model
    max_context_tokens: int = 4000


class DelegationConfig(BaseModel):
    """Which agents this agent can communicate with."""

    can_delegate_to: list[str] = []
    accepts_from: list[str] = []


class ProactiveCheck(BaseModel):
    """A scheduled proactive behavior."""

    trigger: str = "daily"  # frequent (2m) | hourly | daily | weekly
    action: str = ""
    description: str = ""


class LearningConfig(BaseModel):
    """Continuous learning engine configuration.

    When enabled, a local LLM (e.g. ollama/llama3:8b) manages all memory —
    semantic recall before paid-model reasoning, and insight extraction after.
    """

    enabled: bool = True
    memory_model: str = "ollama/llama3:8b"  # local model for memory management
    memory_max_tokens: int = 1024  # max tokens for memory manager responses
    consolidation_interval: int = 20  # every N turns, trigger consolidation
    confidence_decay_days: int = 90  # unvalidated entries decay after this
    max_recall_tokens: int = 4000  # token budget for recalled context
    deep_consolidation_enabled: bool = True  # LLM-driven periodic consolidation
    deep_consolidation_batch_size: int = 10  # entries per LLM call
    deep_consolidation_min_entries: int = 5  # skip if fewer active entries
    archive_confidence_threshold: float = 0.2  # auto-archive below this


class BehaviorConfig(BaseModel):
    """Agent behavior settings."""

    auto_save: bool = True
    first_message: bool = True
    proactive_checks: list[ProactiveCheck] = []


class UIConfig(BaseModel):
    """Agent UI settings."""

    color: str = "#6B7280"
    avatar: str = ""
    sparkle_color: str = "#9CA3AF"


class PersonaConfig(BaseModel):
    """Complete agent persona configuration, loaded from YAML."""

    id: str
    name: str
    title: str = ""
    tagline: str = ""
    type: AgentType = AgentType.ADVISOR
    parent_id: str = ""  # If set, this agent is a sub-agent of the given parent
    model: ModelConfig = ModelConfig()
    voice: VoiceConfig = VoiceConfig()
    vault: VaultConfig = VaultConfig()
    memory: MemoryConfig = MemoryConfig()
    delegation: DelegationConfig = DelegationConfig()
    behavior: BehaviorConfig = BehaviorConfig()
    learning: LearningConfig = LearningConfig()
    reasoning: ReasoningConfig = ReasoningConfig()
    comms: CommsConfig = CommsConfig()
    web: WebConfig = WebConfig()
    integrations: IntegrationConfig = IntegrationConfig()
    ui: UIConfig = UIConfig()
    external: bool = False  # Legacy — use type: external instead
    system_prompt: str = ""

    def load_system_prompt(self, base_dir: str) -> str:
        """Load system prompt from file or return inline prompt.

        base_dir: vault directory containing agent.yaml and instructions.md.
        """
        if self.system_prompt:
            return self.system_prompt
        prompt_path = Path(base_dir) / "instructions.md"
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        return f"You are {self.name}, {self.title}. {self.tagline}"


def _resolve_vault_ref(ref: str, vaults_base: Path) -> str:
    """Resolve a vault reference to an absolute path.

    Supports:
    - "." → the vault's own directory (resolved by caller)
    - "/vaults/{name}" → sibling vault directory
    - "@{name}" → shorthand for sibling vault
    - relative paths → resolved relative to vault dir
    """
    ref = ref.strip()
    if ref.startswith("@"):
        return str(vaults_base / ref[1:])
    parts = ref.replace("\\", "/").strip("/").split("/")
    if len(parts) >= 2 and parts[0] == "vaults":
        return str(vaults_base / "/".join(parts[1:]))
    return ref


def _load_agent_yaml(yaml_path: Path, vault_dir: Path) -> PersonaConfig:
    """Load an agent.yaml from inside a vault directory."""
    vaults_base = vault_dir.parent  # sibling vaults live here

    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Vault path is implicit — it's the directory containing agent.yaml
    vault_data = data.get("vault", {})
    vault_data["path"] = str(vault_dir)
    if "writable_paths" not in vault_data:
        vault_data["writable_paths"] = [str(vault_dir)]
    else:
        vault_data["writable_paths"] = [
            str(vault_dir) if p == "." else _resolve_vault_ref(p, vaults_base)
            for p in vault_data["writable_paths"]
        ]

    # Resolve read_only_mounts paths
    for mount in vault_data.get("read_only_mounts", []):
        mount["path"] = _resolve_vault_ref(mount["path"], vaults_base)

    data["vault"] = vault_data

    # Map legacy external flag to type
    if data.get("external", False) and "type" not in data:
        data["type"] = AgentType.EXTERNAL

    config = PersonaConfig(**data)

    # Auto-wire child delegation: ensure child accepts work from parent
    if config.parent_id:
        if config.parent_id not in config.delegation.accepts_from and "*" not in config.delegation.accepts_from:
            config.delegation.accepts_from.append(config.parent_id)

    # Resolve empty models to the global default
    default = settings.default_model
    if not config.model.reasoning:
        config.model.reasoning = default
    if not config.model.navigator:
        config.model.navigator = default

    return config


def discover_agents_from_vaults(
    vaults_dir: str | Path,
) -> dict[str, PersonaConfig]:
    """Discover agents by scanning vault folders for agent.yaml.

    A subfolder of vaults_dir is an agent iff it contains agent.yaml.
    Folders without agent.yaml (e.g. shared/) are skipped.
    """
    vaults = Path(vaults_dir)
    if not vaults.exists():
        return {}

    agents: dict[str, PersonaConfig] = {}
    for child in sorted(vaults.iterdir()):
        if not child.is_dir():
            continue
        agent_yaml = child / "agent.yaml"
        if not agent_yaml.exists():
            continue
        try:
            config = _load_agent_yaml(agent_yaml, child)
            agents[config.id] = config
            logger.debug("Discovered agent '%s' from %s", config.id, child)
        except Exception:
            logger.exception("Failed to load agent.yaml from %s", child)
    return agents


settings = Settings()

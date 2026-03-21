"""Axon configuration — loaded from environment and persona YAML files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Global settings from environment variables."""

    anthropic_api_key: str = ""
    openai_api_key: str = ""
    ollama_base_url: str = "http://ollama:11434"
    axon_data_dir: str = "/data"
    axon_personas_dir: str = "/personas"
    axon_vaults_dir: str = "/vaults"

    class Config:
        env_file = ".env"


class ModelConfig(BaseModel):
    """Per-agent model configuration."""

    reasoning: str = "anthropic/claude-sonnet-4-20250514"
    navigator: str = "anthropic/claude-sonnet-4-20250514"  # same as reasoning for MVP
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

    path: str
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

    trigger: str = "daily"  # daily | weekly | hourly
    action: str = ""
    description: str = ""


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
    model: ModelConfig = ModelConfig()
    voice: VoiceConfig = VoiceConfig()
    vault: VaultConfig
    memory: MemoryConfig = MemoryConfig()
    delegation: DelegationConfig = DelegationConfig()
    behavior: BehaviorConfig = BehaviorConfig()
    ui: UIConfig = UIConfig()
    system_prompt_file: str = ""
    system_prompt: str = ""

    def load_system_prompt(self, personas_dir: str) -> str:
        """Load system prompt from file or return inline prompt."""
        if self.system_prompt:
            return self.system_prompt
        if self.system_prompt_file:
            prompt_path = Path(personas_dir) / self.system_prompt_file
            if prompt_path.exists():
                return prompt_path.read_text(encoding="utf-8")
        return f"You are {self.name}, {self.title}. {self.tagline}"


def load_persona(yaml_path: str | Path) -> PersonaConfig:
    """Load a persona config from a YAML file."""
    path = Path(yaml_path)
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return PersonaConfig(**data)


def load_all_personas(personas_dir: str | Path) -> dict[str, PersonaConfig]:
    """Load all persona YAML files from a directory."""
    personas: dict[str, PersonaConfig] = {}
    directory = Path(personas_dir)
    for yaml_file in directory.glob("*.yaml"):
        if yaml_file.name.startswith("_"):
            continue  # skip templates
        persona = load_persona(yaml_file)
        personas[persona.id] = persona
    return personas


settings = Settings()

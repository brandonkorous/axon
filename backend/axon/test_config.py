"""Tests for axon.config — path resolution, persona loading, vault discovery."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from axon.config import (
    AgentType,
    PersonaConfig,
    _resolve_vault_for_org,
    _resolve_vault_ref,
    discover_agents_from_vaults,
    load_persona,
)


# ---------------------------------------------------------------------------
# _resolve_vault_for_org
# ---------------------------------------------------------------------------


class TestResolveVaultForOrg:
    def test_vaults_prefix_stripped(self, tmp_path: Path):
        result = _resolve_vault_for_org("/vaults/marcus", tmp_path)
        assert result == str(tmp_path / "marcus")

    def test_vaults_prefix_with_backslashes(self, tmp_path: Path):
        result = _resolve_vault_for_org("\\vaults\\marcus", tmp_path)
        assert result == str(tmp_path / "marcus")

    def test_vaults_nested_path(self, tmp_path: Path):
        result = _resolve_vault_for_org("/vaults/marcus/sub", tmp_path)
        assert result == str(tmp_path / "marcus/sub")

    def test_plain_name_appended(self, tmp_path: Path):
        result = _resolve_vault_for_org("shared", tmp_path)
        assert result == str(tmp_path / "shared")

    def test_strips_leading_trailing_slashes(self, tmp_path: Path):
        result = _resolve_vault_for_org("/shared/", tmp_path)
        assert result == str(tmp_path / "shared")


# ---------------------------------------------------------------------------
# _resolve_vault_ref
# ---------------------------------------------------------------------------


class TestResolveVaultRef:
    def test_at_shorthand(self, tmp_path: Path):
        assert _resolve_vault_ref("@diana", tmp_path) == str(tmp_path / "diana")

    def test_vaults_prefix(self, tmp_path: Path):
        assert _resolve_vault_ref("/vaults/raj", tmp_path) == str(tmp_path / "raj")

    def test_plain_relative_returned_as_is(self, tmp_path: Path):
        assert _resolve_vault_ref("some/relative", tmp_path) == "some/relative"

    def test_dot_returned_as_is(self, tmp_path: Path):
        assert _resolve_vault_ref(".", tmp_path) == "."


# ---------------------------------------------------------------------------
# PersonaConfig.load_system_prompt
# ---------------------------------------------------------------------------


class TestLoadSystemPrompt:
    def test_inline_prompt_takes_priority(self, tmp_path: Path):
        persona = PersonaConfig(
            id="t", name="Test", system_prompt="Use this prompt."
        )
        assert persona.load_system_prompt(str(tmp_path)) == "Use this prompt."

    def test_loads_instructions_md_by_default(self, tmp_path: Path):
        (tmp_path / "instructions.md").write_text("file prompt", encoding="utf-8")
        persona = PersonaConfig(id="t", name="Test")
        assert persona.load_system_prompt(str(tmp_path)) == "file prompt"

    def test_custom_prompt_file(self, tmp_path: Path):
        (tmp_path / "custom.md").write_text("custom content", encoding="utf-8")
        persona = PersonaConfig(id="t", name="Test", system_prompt_file="custom.md")
        assert persona.load_system_prompt(str(tmp_path)) == "custom content"

    def test_fallback_to_legacy_path(self, tmp_path: Path):
        (tmp_path / "t_instructions.md").write_text("legacy", encoding="utf-8")
        persona = PersonaConfig(id="t", name="Test")
        assert persona.load_system_prompt(str(tmp_path)) == "legacy"

    def test_fallback_to_generated_prompt(self):
        persona = PersonaConfig(
            id="t", name="Test", title="Tester", tagline="does things"
        )
        result = persona.load_system_prompt("/nonexistent")
        assert "Test" in result and "Tester" in result


# ---------------------------------------------------------------------------
# load_persona
# ---------------------------------------------------------------------------


class TestLoadPersona:
    def _write_yaml(self, path: Path, data: dict) -> Path:
        yaml_file = path / "agent.yaml"
        yaml_file.write_text(yaml.dump(data), encoding="utf-8")
        return yaml_file

    def test_loads_minimal_persona(self, tmp_path: Path):
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(
            yaml.dump({"id": "marcus", "name": "Marcus", "vault": {"path": "/vaults/marcus"}}),
            encoding="utf-8",
        )
        vaults_base = tmp_path / "vaults"
        vaults_base.mkdir()
        persona = load_persona(yaml_file, vaults_base)
        assert persona.id == "marcus"
        assert persona.name == "Marcus"
        assert str(vaults_base / "marcus") == persona.vault.path

    def test_empty_models_inherit_default(self, tmp_path: Path):
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(
            yaml.dump({"id": "x", "name": "X", "vault": {"path": "x"}}),
            encoding="utf-8",
        )
        persona = load_persona(yaml_file, tmp_path)
        # Both should be populated with the default model
        assert persona.model.reasoning != ""
        assert persona.model.navigator != ""
        assert persona.model.reasoning == persona.model.navigator


# ---------------------------------------------------------------------------
# discover_agents_from_vaults
# ---------------------------------------------------------------------------


class TestDiscoverAgentsFromVaults:
    def test_discovers_agent_yaml(self, tmp_path: Path):
        agent_dir = tmp_path / "marcus"
        agent_dir.mkdir()
        (agent_dir / "agent.yaml").write_text(
            yaml.dump({"id": "marcus", "name": "Marcus"}),
            encoding="utf-8",
        )
        agents = discover_agents_from_vaults(tmp_path)
        assert "marcus" in agents
        assert agents["marcus"].name == "Marcus"
        # Vault path should be the agent directory itself
        assert agents["marcus"].vault.path == str(agent_dir)

    def test_skips_dirs_without_agent_yaml(self, tmp_path: Path):
        (tmp_path / "shared").mkdir()
        (tmp_path / "shared" / "readme.md").write_text("hi", encoding="utf-8")
        agents = discover_agents_from_vaults(tmp_path)
        assert agents == {}

    def test_nonexistent_dir_returns_empty(self):
        agents = discover_agents_from_vaults("/nonexistent/path/that/does/not/exist")
        assert agents == {}

    def test_skips_files_at_top_level(self, tmp_path: Path):
        (tmp_path / "notes.txt").write_text("not an agent", encoding="utf-8")
        agents = discover_agents_from_vaults(tmp_path)
        assert agents == {}

    def test_multiple_agents(self, tmp_path: Path):
        for name in ("alpha", "beta"):
            d = tmp_path / name
            d.mkdir()
            (d / "agent.yaml").write_text(
                yaml.dump({"id": name, "name": name.title()}),
                encoding="utf-8",
            )
        agents = discover_agents_from_vaults(tmp_path)
        assert len(agents) == 2
        assert "alpha" in agents
        assert "beta" in agents

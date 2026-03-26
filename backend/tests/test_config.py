"""Tests for axon.config — path resolution, agent loading, vault discovery."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from axon.config import (
    AgentType,
    PersonaConfig,
    _resolve_vault_ref,
    discover_agents_from_vaults,
)


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

    def test_fallback_to_generated_prompt(self):
        persona = PersonaConfig(
            id="t", name="Test", title="Tester", tagline="does things"
        )
        result = persona.load_system_prompt("/nonexistent")
        assert "Test" in result and "Tester" in result


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

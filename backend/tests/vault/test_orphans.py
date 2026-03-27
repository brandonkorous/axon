"""Tests for orphan detection (VaultGraph.find_orphans) and auto-linking (write_file)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from axon.vault.graph import VaultGraph
from axon.vault.memory_consolidation_actions import (
    ConsolidationReport,
    execute_orphan_adoptions,
)


# ── Helpers ──────────────────────────────────────────────────────


def _write_md(path: Path, body: str, frontmatter: dict[str, str] | None = None) -> None:
    """Write a markdown file, optionally with YAML frontmatter."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    if frontmatter:
        lines.append("---")
        for k, v in frontmatter.items():
            lines.append(f"{k}: {v}")
        lines.append("---")
    lines.append(body)
    path.write_text("\n".join(lines), encoding="utf-8")


def _scaffold_vault(tmp_path: Path) -> Path:
    """Create a minimal vault with root → branch index → leaf."""
    _write_md(
        tmp_path / "second-brain.md",
        "# Root\n\n## Branches\n- [[learnings/learnings-index]]\n",
    )
    _write_md(
        tmp_path / "learnings" / "learnings-index.md",
        "# Learnings\n- [[insight-a]]\n",
        {"name": "Learnings Index"},
    )
    _write_md(
        tmp_path / "learnings" / "insight-a.md",
        "## Insight\nSome insight.",
        {"name": "Insight A", "description": "First insight"},
    )
    return tmp_path


# ── VaultGraph.find_orphans ──────────────────────────────────────


class TestFindOrphans:
    def test_no_orphans_in_connected_vault(self, tmp_path):
        vault = _scaffold_vault(tmp_path)
        graph = VaultGraph.build(vault)
        assert graph.find_orphans("second-brain.md") == []

    def test_detects_unlinked_file(self, tmp_path):
        vault = _scaffold_vault(tmp_path)
        _write_md(vault / "stray.md", "I am lost.", {"name": "Stray"})

        graph = VaultGraph.build(vault)
        orphans = graph.find_orphans("second-brain.md")

        assert len(orphans) == 1
        assert orphans[0].path == "stray.md"

    def test_detects_unlinked_branch_file(self, tmp_path):
        vault = _scaffold_vault(tmp_path)
        # File exists in branch dir but not referenced from the index
        _write_md(
            vault / "learnings" / "insight-b.md",
            "## Insight\nAnother insight.",
            {"name": "Insight B"},
        )

        graph = VaultGraph.build(vault)
        orphans = graph.find_orphans("second-brain.md")

        assert len(orphans) == 1
        assert orphans[0].name == "insight-b"

    def test_file_linked_via_backlink_is_not_orphan(self, tmp_path):
        vault = _scaffold_vault(tmp_path)
        # insight-a links to standalone file → reachable via backlinks from root
        _write_md(vault / "learnings" / "insight-a.md", "See also [[deep-note]]")
        _write_md(vault / "learnings" / "deep-note.md", "Deep thought.")

        graph = VaultGraph.build(vault)
        assert graph.find_orphans("second-brain.md") == []

    def test_missing_root_returns_empty(self, tmp_path):
        _write_md(tmp_path / "lonely.md", "No root here.")
        graph = VaultGraph.build(tmp_path)
        assert graph.find_orphans("second-brain.md") == []

    def test_instructions_detected_as_orphan(self, tmp_path):
        """Reproduces the original bug — instructions.md with no link from root."""
        vault = _scaffold_vault(tmp_path)
        _write_md(vault / "instructions.md", "You are Agent X.")

        graph = VaultGraph.build(vault)
        orphans = graph.find_orphans("second-brain.md")

        assert any(o.name == "instructions" for o in orphans)

    def test_instructions_not_orphan_when_linked(self, tmp_path):
        """After template fix, instructions linked from root is reachable."""
        vault = _scaffold_vault(tmp_path)
        # Append instructions link to root
        root = vault / "second-brain.md"
        content = root.read_text(encoding="utf-8")
        root.write_text(content + "\n## Agent Identity\n- [[instructions]]\n", encoding="utf-8")
        _write_md(vault / "instructions.md", "You are Agent X.")

        graph = VaultGraph.build(vault)
        assert graph.find_orphans("second-brain.md") == []


# ── execute_orphan_adoptions ─────────────────────────────────────


class TestExecuteOrphanAdoptions:
    def _make_vault_manager(self, tmp_path: Path):
        """Create a real VaultManager for integration-style tests."""
        from axon.vault.vault import VaultManager

        _scaffold_vault(tmp_path)
        return VaultManager(str(tmp_path))

    def test_adopt_into_branch(self, tmp_path):
        vault = self._make_vault_manager(tmp_path)
        # Create an orphan
        _write_md(
            tmp_path / "learnings" / "insight-orphan.md",
            "Orphan insight.",
            {"name": "Orphan Insight", "description": "An orphaned insight"},
        )
        vault.cache.load_all()

        report = ConsolidationReport()
        adoptions = [
            {
                "path": "learnings/insight-orphan.md",
                "action": "adopt",
                "target_branch": "learnings",
                "reason": "Belongs in learnings",
            }
        ]
        execute_orphan_adoptions(vault, adoptions, "2026-03-26", report)

        assert report.orphans_adopted == 1
        # Verify it's now in the index
        index = (tmp_path / "learnings" / "learnings-index.md").read_text(encoding="utf-8")
        assert "[[insight-orphan]]" in index

    def test_link_to_root(self, tmp_path):
        vault = self._make_vault_manager(tmp_path)
        _write_md(tmp_path / "instructions.md", "Agent identity.")
        vault.cache.load_all()

        report = ConsolidationReport()
        adoptions = [
            {
                "path": "instructions.md",
                "action": "link_root",
                "reason": "Top-level identity doc",
            }
        ]
        execute_orphan_adoptions(vault, adoptions, "2026-03-26", report)

        assert report.orphans_linked_root == 1
        root = (tmp_path / "second-brain.md").read_text(encoding="utf-8")
        assert "[[instructions]]" in root

    def test_link_root_idempotent(self, tmp_path):
        vault = self._make_vault_manager(tmp_path)
        _write_md(tmp_path / "instructions.md", "Agent identity.")
        vault.cache.load_all()

        report = ConsolidationReport()
        adoption = {
            "path": "instructions.md",
            "action": "link_root",
            "reason": "Top-level identity doc",
        }
        execute_orphan_adoptions(vault, [adoption], "2026-03-26", report)
        execute_orphan_adoptions(vault, [adoption], "2026-03-26", report)

        root = (tmp_path / "second-brain.md").read_text(encoding="utf-8")
        assert root.count("[[instructions]]") == 1

    def test_archive_orphan(self, tmp_path):
        vault = self._make_vault_manager(tmp_path)
        _write_md(
            tmp_path / "learnings" / "stale.md",
            "",
            {"name": "Stale", "status": "active"},
        )
        vault.cache.load_all()

        report = ConsolidationReport()
        adoptions = [
            {
                "path": "learnings/stale.md",
                "action": "archive",
                "reason": "Empty, no content",
            }
        ]
        execute_orphan_adoptions(vault, adoptions, "2026-03-26", report)

        assert report.orphans_archived == 1
        meta, _ = vault.read_file("learnings/stale.md")
        assert meta["status"] == "archived"

    def test_skips_invalid_action(self, tmp_path):
        vault = self._make_vault_manager(tmp_path)
        report = ConsolidationReport()
        adoptions = [{"path": "nonexistent.md", "action": "unknown"}]
        # Should not raise
        execute_orphan_adoptions(vault, adoptions, "2026-03-26", report)
        assert report.orphans_adopted == 0


# ── write_file auto-linking ──────────────────────────────────────


class TestWriteFileAutoLink:
    def test_new_file_auto_linked_to_branch_index(self, tmp_path):
        from axon.vault.vault import VaultManager

        _scaffold_vault(tmp_path)
        vault = VaultManager(str(tmp_path))

        vault.write_file(
            "learnings/auto-linked.md",
            {"name": "Auto Linked", "description": "Should appear in index"},
            "Content here.",
        )

        index = (tmp_path / "learnings" / "learnings-index.md").read_text(encoding="utf-8")
        assert "[[auto-linked]]" in index

    def test_existing_file_not_double_indexed(self, tmp_path):
        from axon.vault.vault import VaultManager

        _scaffold_vault(tmp_path)
        vault = VaultManager(str(tmp_path))

        # Write once (new file → auto-linked)
        vault.write_file(
            "learnings/entry.md",
            {"name": "Entry", "description": "Desc"},
            "v1",
        )
        # Write again (update → no re-index)
        vault.write_file(
            "learnings/entry.md",
            {"name": "Entry", "description": "Desc"},
            "v2",
        )

        index = (tmp_path / "learnings" / "learnings-index.md").read_text(encoding="utf-8")
        assert index.count("[[entry]]") == 1

    def test_root_level_file_not_auto_linked(self, tmp_path):
        from axon.vault.vault import VaultManager

        _scaffold_vault(tmp_path)
        vault = VaultManager(str(tmp_path))

        vault.write_file("notes.md", {"name": "Notes"}, "Root level.")

        root = (tmp_path / "second-brain.md").read_text(encoding="utf-8")
        assert "[[notes]]" not in root  # Root-level files need explicit linking

    def test_index_file_not_indexed_into_itself(self, tmp_path):
        from axon.vault.vault import VaultManager

        _scaffold_vault(tmp_path)
        vault = VaultManager(str(tmp_path))

        # Creating a new branch index shouldn't try to index itself
        vault.write_file(
            "decisions/decisions-index.md",
            {"name": "Decisions Index"},
            "# Decisions\n",
        )

        content = (tmp_path / "decisions" / "decisions-index.md").read_text(encoding="utf-8")
        assert "[[decisions-index]]" not in content

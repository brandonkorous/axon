"""Tests for axon.vault.index — automatic index file maintenance."""

from __future__ import annotations

import pytest

from axon.vault.index import ensure_index_entry


class TestEnsureIndexEntry:
    def _make_index(self, tmp_path, branch: str, suffix: str, content: str) -> None:
        """Helper to create a branch directory with an index file."""
        branch_dir = tmp_path / branch
        branch_dir.mkdir(parents=True, exist_ok=True)
        (branch_dir / f"{branch}-{suffix}.md").write_text(content, encoding="utf-8")

    def test_adds_entry_to_index(self, tmp_path):
        self._make_index(tmp_path, "decisions", "index", "# Decisions Index\n")
        ensure_index_entry(tmp_path, "decisions", "pricing-model.md", "Pricing strategy")
        content = (tmp_path / "decisions" / "decisions-index.md").read_text(encoding="utf-8")
        assert "[[pricing-model]]" in content
        assert "Pricing strategy" in content

    def test_idempotent_no_duplicates(self, tmp_path):
        self._make_index(tmp_path, "decisions", "index", "# Decisions Index\n")
        ensure_index_entry(tmp_path, "decisions", "pricing.md", "Pricing v1")
        ensure_index_entry(tmp_path, "decisions", "pricing.md", "Pricing v1")
        content = (tmp_path / "decisions" / "decisions-index.md").read_text(encoding="utf-8")
        assert content.count("[[pricing]]") == 1

    def test_entry_format(self, tmp_path):
        self._make_index(tmp_path, "learnings", "index", "# Learnings\n")
        ensure_index_entry(tmp_path, "learnings", "2026-03-20-insight.md", "Key insight")
        content = (tmp_path / "learnings" / "learnings-index.md").read_text(encoding="utf-8")
        assert "- [[2026-03-20-insight]] — Key insight" in content

    def test_strips_md_extension(self, tmp_path):
        self._make_index(tmp_path, "branch", "index", "# Index\n")
        ensure_index_entry(tmp_path, "branch", "file.md", "Desc")
        content = (tmp_path / "branch" / "branch-index.md").read_text(encoding="utf-8")
        assert "[[file]]" in content
        assert "[[file.md]]" not in content

    def test_falls_back_to_log_file(self, tmp_path):
        branch_dir = tmp_path / "ops"
        branch_dir.mkdir()
        (branch_dir / "ops-log.md").write_text("# Ops Log\n", encoding="utf-8")
        ensure_index_entry(tmp_path, "ops", "deploy-v2.md", "Deployed v2")
        content = (branch_dir / "ops-log.md").read_text(encoding="utf-8")
        assert "[[deploy-v2]]" in content

    def test_falls_back_to_branch_file(self, tmp_path):
        branch_dir = tmp_path / "notes"
        branch_dir.mkdir()
        (branch_dir / "notes.md").write_text("# Notes\n", encoding="utf-8")
        ensure_index_entry(tmp_path, "notes", "idea.md", "An idea")
        content = (branch_dir / "notes.md").read_text(encoding="utf-8")
        assert "[[idea]]" in content

    def test_no_index_file_does_nothing(self, tmp_path):
        branch_dir = tmp_path / "empty"
        branch_dir.mkdir()
        # Should not raise even if no index file exists
        ensure_index_entry(tmp_path, "empty", "orphan.md", "Orphan entry")

    def test_preserves_existing_content(self, tmp_path):
        initial = "# Index\n- [[existing]] — Already here\n"
        self._make_index(tmp_path, "branch", "index", initial)
        ensure_index_entry(tmp_path, "branch", "new-entry.md", "New")
        content = (tmp_path / "branch" / "branch-index.md").read_text(encoding="utf-8")
        assert "[[existing]] — Already here" in content
        assert "[[new-entry]] — New" in content

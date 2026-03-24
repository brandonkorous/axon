"""Tests for axon.audit — AuditLogger log, list_entries, count, helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from axon.audit import AUDIT_BRANCH, AuditLogger, is_audit_branch


@pytest.fixture
def logger(tmp_path: Path) -> AuditLogger:
    return AuditLogger(tmp_path)


# ---------------------------------------------------------------------------
# log()
# ---------------------------------------------------------------------------


class TestLog:
    def test_creates_md_file(self, logger: AuditLogger, tmp_path: Path):
        rel = logger.log(agent_id="marcus", action="file_read", tool="vault_read")
        full_path = tmp_path / rel
        assert full_path.exists()
        assert full_path.suffix == ".md"

    def test_returns_relative_path_under_audit_branch(self, logger: AuditLogger):
        rel = logger.log(agent_id="marcus", action="file_read", tool="vault_read")
        assert rel.startswith(f"{AUDIT_BRANCH}/")

    def test_file_contains_frontmatter_fields(self, logger: AuditLogger, tmp_path: Path):
        rel = logger.log(
            agent_id="marcus",
            action="file_write",
            tool="vault_write",
            context="testing",
            arguments='{"path": "/foo"}',
            result_summary="ok",
        )
        content = (tmp_path / rel).read_text(encoding="utf-8")
        assert "agent_id: marcus" in content
        assert "action: file_write" in content
        assert "tool: vault_write" in content
        assert "## Context" in content
        assert "## Arguments" in content
        assert "## Result" in content

    def test_action_slug_in_filename(self, logger: AuditLogger):
        rel = logger.log(agent_id="a", action="file read", tool="t")
        filename = Path(rel).name
        assert "file-read" in filename

    def test_long_arguments_truncated(self, logger: AuditLogger, tmp_path: Path):
        long_args = "x" * 3000
        rel = logger.log(agent_id="a", action="a", tool="t", arguments=long_args)
        content = (tmp_path / rel).read_text(encoding="utf-8")
        assert "truncated" in content.lower()

    def test_long_result_truncated(self, logger: AuditLogger, tmp_path: Path):
        long_result = "y" * 2000
        rel = logger.log(agent_id="a", action="a", tool="t", result_summary=long_result)
        content = (tmp_path / rel).read_text(encoding="utf-8")
        assert "truncated" in content.lower()


# ---------------------------------------------------------------------------
# list_entries()
# ---------------------------------------------------------------------------


class TestListEntries:
    def _seed(self, logger: AuditLogger):
        """Create several audit entries."""
        logger.log(agent_id="marcus", action="read", tool="vault_read")
        logger.log(agent_id="raj", action="write", tool="vault_write")
        logger.log(agent_id="marcus", action="delete", tool="vault_delete")

    def test_lists_all_entries(self, logger: AuditLogger):
        self._seed(logger)
        entries = logger.list_entries()
        assert len(entries) == 3

    def test_filter_by_agent(self, logger: AuditLogger):
        self._seed(logger)
        entries = logger.list_entries(agent_id="marcus")
        assert len(entries) == 2
        assert all(e["agent_id"] == "marcus" for e in entries)

    def test_filter_by_action(self, logger: AuditLogger):
        self._seed(logger)
        entries = logger.list_entries(action="write")
        assert len(entries) == 1
        assert entries[0]["agent_id"] == "raj"

    def test_filter_by_tool(self, logger: AuditLogger):
        self._seed(logger)
        entries = logger.list_entries(tool="vault_delete")
        assert len(entries) == 1

    def test_pagination(self, logger: AuditLogger):
        self._seed(logger)
        page = logger.list_entries(limit=2)
        assert len(page) == 2
        page2 = logger.list_entries(limit=2, offset=2)
        assert len(page2) == 1

    def test_empty_audit_dir(self, logger: AuditLogger):
        assert logger.list_entries() == []

    def test_date_filter(self, logger: AuditLogger, tmp_path: Path):
        """Entries outside the date window are excluded."""
        # Create entries in two different date dirs manually
        from axon.vault.frontmatter import write_file_with_frontmatter

        for day in ("2025-06-01", "2025-06-02"):
            day_dir = tmp_path / AUDIT_BRANCH / day
            day_dir.mkdir(parents=True, exist_ok=True)
            write_file_with_frontmatter(
                str(day_dir / f"20250601000000-test.md"),
                {"agent_id": "a", "action": "test", "tool": "t", "type": "audit"},
                "",
            )
        entries = logger.list_entries(date_from="2025-06-02", date_to="2025-06-02")
        assert len(entries) == 1


# ---------------------------------------------------------------------------
# count_entries()
# ---------------------------------------------------------------------------


class TestCountEntries:
    def test_zero_when_empty(self, logger: AuditLogger):
        assert logger.count_entries() == 0

    def test_counts_all(self, logger: AuditLogger):
        logger.log(agent_id="a", action="a", tool="t")
        logger.log(agent_id="b", action="b", tool="t")
        assert logger.count_entries() == 2


# ---------------------------------------------------------------------------
# is_audit_branch()
# ---------------------------------------------------------------------------


class TestIsAuditBranch:
    def test_exact_match(self):
        assert is_audit_branch("audit") is True

    def test_subpath(self):
        assert is_audit_branch("audit/2025-06-01/file.md") is True

    def test_with_backslashes(self):
        assert is_audit_branch("audit\\2025-06-01\\file.md") is True

    def test_leading_slash(self):
        assert is_audit_branch("/audit/foo") is True

    def test_non_audit(self):
        assert is_audit_branch("memory/foo.md") is False

    def test_partial_match_not_audit(self):
        assert is_audit_branch("auditing/foo.md") is False

"""Tests for axon.vault.memory_learning — outcome linking and confidence math."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from axon.config import LearningConfig
from axon.vault.memory_learning import apply_confidence_decay, link_outcome


def _make_vault(tmp_path: Path) -> MagicMock:
    """Create a minimal VaultManager mock backed by a dict of files."""
    store: dict[str, tuple[dict[str, Any], str]] = {}
    vault = MagicMock()
    vault.vault_path = str(tmp_path)
    vault.root_file = "second-brain.md"

    def read_file(path: str) -> tuple[dict[str, Any], str]:
        if path not in store:
            raise FileNotFoundError(path)
        meta, body = store[path]
        # Return a copy so mutations in the code under test are captured via write
        return dict(meta), body

    def write_file(path: str, metadata: dict[str, Any], body: str, **kw: Any) -> str:
        store[path] = (metadata, body)
        return path

    vault.read_file = MagicMock(side_effect=read_file)
    vault.write_file = MagicMock(side_effect=write_file)
    vault._store = store  # Expose for test setup
    return vault


class TestLinkOutcome:
    @pytest.mark.asyncio
    async def test_positive_outcome_increases_confidence(self, tmp_path):
        vault = _make_vault(tmp_path)
        vault._store["decisions/pricing.md"] = (
            {"confidence": 0.5, "confidence_history": []},
            "Body text.",
        )
        result = await link_outcome(vault, "outcomes/q1-revenue.md", ["decisions/pricing.md"], "positive")
        meta, _ = vault._store["decisions/pricing.md"]
        assert meta["confidence"] == 0.65  # 0.5 + 0.15
        assert "Updated 1 files" in result

    @pytest.mark.asyncio
    async def test_negative_outcome_decreases_confidence(self, tmp_path):
        vault = _make_vault(tmp_path)
        vault._store["decisions/hiring.md"] = (
            {"confidence": 0.7, "confidence_history": []},
            "Body.",
        )
        result = await link_outcome(vault, "outcomes/bad-hire.md", ["decisions/hiring.md"], "negative")
        meta, _ = vault._store["decisions/hiring.md"]
        assert meta["confidence"] == 0.5  # 0.7 - 0.2

    @pytest.mark.asyncio
    async def test_mixed_outcome_small_increase(self, tmp_path):
        vault = _make_vault(tmp_path)
        vault._store["decisions/launch.md"] = (
            {"confidence": 0.6, "confidence_history": []},
            "Body.",
        )
        await link_outcome(vault, "outcomes/mixed.md", ["decisions/launch.md"], "mixed")
        meta, _ = vault._store["decisions/launch.md"]
        assert meta["confidence"] == 0.65  # 0.6 + 0.05

    @pytest.mark.asyncio
    async def test_confidence_clamped_at_upper_bound(self, tmp_path):
        vault = _make_vault(tmp_path)
        vault._store["decisions/great.md"] = (
            {"confidence": 0.9, "confidence_history": []},
            "Body.",
        )
        await link_outcome(vault, "outcomes/win.md", ["decisions/great.md"], "positive")
        meta, _ = vault._store["decisions/great.md"]
        assert meta["confidence"] == 0.95  # clamped at max

    @pytest.mark.asyncio
    async def test_confidence_clamped_at_lower_bound(self, tmp_path):
        vault = _make_vault(tmp_path)
        vault._store["decisions/bad.md"] = (
            {"confidence": 0.1, "confidence_history": []},
            "Body.",
        )
        await link_outcome(vault, "outcomes/fail.md", ["decisions/bad.md"], "negative")
        meta, _ = vault._store["decisions/bad.md"]
        assert meta["confidence"] == 0.0  # 0.1 - 0.2 clamped to 0.0

    @pytest.mark.asyncio
    async def test_confidence_history_appended(self, tmp_path):
        vault = _make_vault(tmp_path)
        vault._store["decisions/test.md"] = (
            {"confidence": 0.5, "confidence_history": [{"date": "2026-01-01", "value": 0.5, "reason": "initial"}]},
            "Body.",
        )
        await link_outcome(vault, "outcomes/result.md", ["decisions/test.md"], "positive")
        meta, _ = vault._store["decisions/test.md"]
        assert len(meta["confidence_history"]) == 2
        latest = meta["confidence_history"][-1]
        assert latest["value"] == 0.65
        assert "positive outcome" in latest["reason"]

    @pytest.mark.asyncio
    async def test_validated_by_added_for_positive(self, tmp_path):
        vault = _make_vault(tmp_path)
        vault._store["decisions/test.md"] = (
            {"confidence": 0.5, "confidence_history": []},
            "Body.",
        )
        await link_outcome(vault, "outcomes/good.md", ["decisions/test.md"], "positive")
        meta, _ = vault._store["decisions/test.md"]
        assert "[[good]]" in meta["validated_by"]

    @pytest.mark.asyncio
    async def test_contradicted_by_added_for_negative(self, tmp_path):
        vault = _make_vault(tmp_path)
        vault._store["decisions/test.md"] = (
            {"confidence": 0.5, "confidence_history": []},
            "Body.",
        )
        await link_outcome(vault, "outcomes/bad.md", ["decisions/test.md"], "negative")
        meta, _ = vault._store["decisions/test.md"]
        assert "[[bad]]" in meta["contradicted_by"]

    @pytest.mark.asyncio
    async def test_multiple_related_paths(self, tmp_path):
        vault = _make_vault(tmp_path)
        vault._store["a.md"] = ({"confidence": 0.5, "confidence_history": []}, "A")
        vault._store["b.md"] = ({"confidence": 0.6, "confidence_history": []}, "B")
        result = await link_outcome(vault, "outcomes/o.md", ["a.md", "b.md"], "positive")
        assert "Updated 2 files" in result
        assert vault._store["a.md"][0]["confidence"] == 0.65
        assert vault._store["b.md"][0]["confidence"] == 0.75

    @pytest.mark.asyncio
    async def test_unknown_outcome_type_no_change(self, tmp_path):
        vault = _make_vault(tmp_path)
        vault._store["decisions/test.md"] = (
            {"confidence": 0.5, "confidence_history": []},
            "Body.",
        )
        await link_outcome(vault, "outcomes/x.md", ["decisions/test.md"], "unknown_type")
        meta, _ = vault._store["decisions/test.md"]
        assert meta["confidence"] == 0.5  # delta is 0.0

    @pytest.mark.asyncio
    async def test_missing_file_graceful(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = await link_outcome(vault, "outcomes/x.md", ["nonexistent.md"], "positive")
        assert result == "No files updated."


class TestApplyConfidenceDecay:
    def test_decays_old_unvalidated_entry(self, tmp_path):
        vault = _make_vault(tmp_path)
        old_date = str(date.today() - timedelta(days=100))
        vault._store["learnings/old.md"] = (
            {"confidence": 0.7, "last_validated": old_date, "confidence_history": []},
            "Body.",
        )
        config = LearningConfig(confidence_decay_days=90)
        apply_confidence_decay(vault, config, [{"path": "learnings/old.md"}])
        meta, _ = vault._store["learnings/old.md"]
        assert meta["confidence"] == 0.6  # 0.7 - 0.1

    def test_no_decay_within_threshold(self, tmp_path):
        vault = _make_vault(tmp_path)
        recent_date = str(date.today() - timedelta(days=30))
        vault._store["learnings/recent.md"] = (
            {"confidence": 0.7, "last_validated": recent_date, "confidence_history": []},
            "Body.",
        )
        config = LearningConfig(confidence_decay_days=90)
        apply_confidence_decay(vault, config, [{"path": "learnings/recent.md"}])
        meta, _ = vault._store["learnings/recent.md"]
        assert meta["confidence"] == 0.7  # Unchanged

    def test_no_decay_if_validated_by_present(self, tmp_path):
        vault = _make_vault(tmp_path)
        old_date = str(date.today() - timedelta(days=200))
        vault._store["learnings/validated.md"] = (
            {"confidence": 0.8, "last_validated": old_date, "validated_by": ["[[proof]]"], "confidence_history": []},
            "Body.",
        )
        config = LearningConfig(confidence_decay_days=90)
        apply_confidence_decay(vault, config, [{"path": "learnings/validated.md"}])
        meta, _ = vault._store["learnings/validated.md"]
        assert meta["confidence"] == 0.8  # Protected by validated_by

    def test_decay_clamped_at_zero(self, tmp_path):
        vault = _make_vault(tmp_path)
        old_date = str(date.today() - timedelta(days=200))
        vault._store["learnings/low.md"] = (
            {"confidence": 0.0, "last_validated": old_date, "confidence_history": []},
            "Body.",
        )
        config = LearningConfig(confidence_decay_days=90)
        apply_confidence_decay(vault, config, [{"path": "learnings/low.md"}])
        meta, _ = vault._store["learnings/low.md"]
        assert meta["confidence"] == 0.0  # Already at floor, no write

    def test_skips_entries_without_path(self, tmp_path):
        vault = _make_vault(tmp_path)
        config = LearningConfig(confidence_decay_days=90)
        # Should not raise
        apply_confidence_decay(vault, config, [{"path": ""}, {}])

    def test_skips_entries_without_last_validated(self, tmp_path):
        vault = _make_vault(tmp_path)
        vault._store["learnings/no-date.md"] = (
            {"confidence": 0.7, "confidence_history": []},
            "Body.",
        )
        config = LearningConfig(confidence_decay_days=90)
        apply_confidence_decay(vault, config, [{"path": "learnings/no-date.md"}])
        meta, _ = vault._store["learnings/no-date.md"]
        assert meta["confidence"] == 0.7  # Unchanged — no last_validated

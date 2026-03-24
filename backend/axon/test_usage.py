"""Tests for axon.usage — UsageTracker record, query, and summary."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from axon.usage import UsageTracker


@pytest.fixture
def tracker(tmp_path: Path) -> UsageTracker:
    return UsageTracker(tmp_path)


# ---------------------------------------------------------------------------
# record()
# ---------------------------------------------------------------------------


class TestRecord:
    def test_creates_jsonl_file(self, tracker: UsageTracker, tmp_path: Path):
        tracker.record(model="gpt-4", prompt_tokens=10, completion_tokens=5, total_tokens=15)
        files = list((tmp_path / "usage").glob("*.jsonl"))
        assert len(files) == 1

    def test_record_fields_serialized(self, tracker: UsageTracker, tmp_path: Path):
        tracker.record(
            model="claude-sonnet",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            cost=0.003,
            agent_id="marcus",
            org_id="acme",
            call_type="completion",
            caller="chat",
        )
        files = list((tmp_path / "usage").glob("*.jsonl"))
        line = files[0].read_text(encoding="utf-8").strip()
        rec = json.loads(line)
        assert rec["model"] == "claude-sonnet"
        assert rec["prompt_tokens"] == 100
        assert rec["completion_tokens"] == 50
        assert rec["total_tokens"] == 150
        assert rec["cost"] == 0.003
        assert rec["agent_id"] == "marcus"
        assert rec["org_id"] == "acme"
        assert rec["ts"].endswith("Z")

    def test_multiple_records_append(self, tracker: UsageTracker, tmp_path: Path):
        tracker.record(model="a", total_tokens=1)
        tracker.record(model="b", total_tokens=2)
        files = list((tmp_path / "usage").glob("*.jsonl"))
        lines = files[0].read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2


# ---------------------------------------------------------------------------
# query()
# ---------------------------------------------------------------------------


class TestQuery:
    def _seed(self, tracker: UsageTracker, tmp_path: Path):
        """Write a hand-crafted JSONL file for deterministic querying."""
        usage_dir = tmp_path / "usage"
        usage_dir.mkdir(parents=True, exist_ok=True)
        records = [
            {"ts": "2025-06-01T10:00:00Z", "model": "gpt-4", "agent_id": "marcus", "total_tokens": 100, "cost": 0.01},
            {"ts": "2025-06-01T11:00:00Z", "model": "claude", "agent_id": "raj", "total_tokens": 200, "cost": 0.02},
            {"ts": "2025-06-01T12:00:00Z", "model": "gpt-4", "agent_id": "marcus", "total_tokens": 300, "cost": 0.03},
        ]
        path = usage_dir / "2025-06-01.jsonl"
        path.write_text(
            "\n".join(json.dumps(r) for r in records) + "\n",
            encoding="utf-8",
        )

    def test_query_all(self, tracker: UsageTracker, tmp_path: Path):
        self._seed(tracker, tmp_path)
        result = tracker.query()
        assert result["total"] == 3
        assert len(result["records"]) == 3

    def test_filter_by_agent(self, tracker: UsageTracker, tmp_path: Path):
        self._seed(tracker, tmp_path)
        result = tracker.query(agent_id="marcus")
        assert result["total"] == 2
        assert all(r["agent_id"] == "marcus" for r in result["records"])

    def test_filter_by_model(self, tracker: UsageTracker, tmp_path: Path):
        self._seed(tracker, tmp_path)
        result = tracker.query(model="claude")
        assert result["total"] == 1
        assert result["records"][0]["model"] == "claude"

    def test_filter_by_date_range(self, tracker: UsageTracker, tmp_path: Path):
        """Records outside the date range are excluded."""
        usage_dir = tmp_path / "usage"
        usage_dir.mkdir(parents=True, exist_ok=True)
        for day in ("2025-06-01", "2025-06-02", "2025-06-03"):
            (usage_dir / f"{day}.jsonl").write_text(
                json.dumps({"ts": f"{day}T00:00:00Z", "model": "m", "agent_id": "a", "total_tokens": 1, "cost": 0}) + "\n",
                encoding="utf-8",
            )
        result = tracker.query(date_from="2025-06-02", date_to="2025-06-02")
        assert result["total"] == 1

    def test_pagination_limit(self, tracker: UsageTracker, tmp_path: Path):
        self._seed(tracker, tmp_path)
        result = tracker.query(limit=2)
        assert len(result["records"]) == 2
        assert result["total"] == 3

    def test_pagination_offset(self, tracker: UsageTracker, tmp_path: Path):
        self._seed(tracker, tmp_path)
        result = tracker.query(limit=10, offset=2)
        assert len(result["records"]) == 1
        assert result["total"] == 3


# ---------------------------------------------------------------------------
# summary()
# ---------------------------------------------------------------------------


class TestSummary:
    def _seed(self, tracker: UsageTracker, tmp_path: Path):
        usage_dir = tmp_path / "usage"
        usage_dir.mkdir(parents=True, exist_ok=True)
        records = [
            {"ts": "2025-06-01T10:00:00Z", "model": "gpt-4", "agent_id": "marcus", "total_tokens": 100, "cost": 0.01},
            {"ts": "2025-06-01T11:00:00Z", "model": "claude", "agent_id": "raj", "total_tokens": 200, "cost": 0.05},
            {"ts": "2025-06-01T12:00:00Z", "model": "gpt-4", "agent_id": "marcus", "total_tokens": 300, "cost": 0.03},
        ]
        (usage_dir / "2025-06-01.jsonl").write_text(
            "\n".join(json.dumps(r) for r in records) + "\n",
            encoding="utf-8",
        )

    def test_totals(self, tracker: UsageTracker, tmp_path: Path):
        self._seed(tracker, tmp_path)
        s = tracker.summary()
        assert s["total_requests"] == 3
        assert s["total_tokens"] == 600
        assert s["total_cost"] == pytest.approx(0.09, abs=1e-6)

    def test_by_model_aggregation(self, tracker: UsageTracker, tmp_path: Path):
        self._seed(tracker, tmp_path)
        s = tracker.summary()
        assert "gpt-4" in s["by_model"]
        assert s["by_model"]["gpt-4"]["count"] == 2
        assert s["by_model"]["gpt-4"]["tokens"] == 400

    def test_by_agent_aggregation(self, tracker: UsageTracker, tmp_path: Path):
        self._seed(tracker, tmp_path)
        s = tracker.summary()
        assert s["by_agent"]["marcus"]["count"] == 2
        assert s["by_agent"]["raj"]["count"] == 1

    def test_empty_usage_dir(self, tracker: UsageTracker):
        s = tracker.summary()
        assert s["total_requests"] == 0
        assert s["total_cost"] == 0.0
        assert s["by_model"] == {}

    def test_summary_date_filter(self, tracker: UsageTracker, tmp_path: Path):
        usage_dir = tmp_path / "usage"
        usage_dir.mkdir(parents=True, exist_ok=True)
        for day, cost in [("2025-06-01", 0.01), ("2025-06-02", 0.02)]:
            (usage_dir / f"{day}.jsonl").write_text(
                json.dumps({"ts": f"{day}T00:00:00Z", "model": "m", "agent_id": "a", "total_tokens": 10, "cost": cost}) + "\n",
                encoding="utf-8",
            )
        s = tracker.summary(date_from="2025-06-02", date_to="2025-06-02")
        assert s["total_requests"] == 1
        assert s["total_cost"] == pytest.approx(0.02, abs=1e-6)

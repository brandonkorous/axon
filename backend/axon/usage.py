"""Append-only LLM usage tracker — writes JSONL records to data/usage/{date}.jsonl."""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, date
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Default cost for models where litellm can't calculate (e.g. Ollama)
ZERO_COST = 0.0


class UsageTracker:
    """Tracks LLM token usage and cost per request.

    Writes one JSON object per line to usage/{YYYY-MM-DD}.jsonl.
    Thread-safe via a simple lock for concurrent agent calls.
    """

    def __init__(self, data_dir: str | Path):
        self.usage_dir = Path(data_dir) / "usage"
        self._lock = threading.Lock()

    def record(
        self,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        cost: float = 0.0,
        agent_id: str = "",
        org_id: str = "",
        call_type: str = "completion",
        caller: str = "",
    ) -> None:
        """Append a usage record to today's JSONL file."""
        ts = datetime.utcnow()
        record = {
            "ts": ts.isoformat() + "Z",
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cost": round(cost, 8),
            "agent_id": agent_id,
            "org_id": org_id,
            "call_type": call_type,
            "caller": caller,
        }

        self.usage_dir.mkdir(parents=True, exist_ok=True)
        file_path = self.usage_dir / f"{ts.strftime('%Y-%m-%d')}.jsonl"

        line = json.dumps(record, separators=(",", ":")) + "\n"
        with self._lock:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(line)

        logger.debug(
            "Usage: model=%s tokens=%d cost=$%.6f agent=%s",
            model, total_tokens, cost, agent_id,
        )

    def _iter_records(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
    ):
        """Yield all records within the date range, newest first."""
        if not self.usage_dir.exists():
            return

        files = sorted(self.usage_dir.glob("*.jsonl"), reverse=True)
        for file_path in files:
            day = file_path.stem  # YYYY-MM-DD
            if date_from and day < date_from:
                continue
            if date_to and day > date_to:
                continue

            lines = file_path.read_text(encoding="utf-8").strip().splitlines()
            for line in reversed(lines):  # newest first within each day
                if not line.strip():
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue

    def query(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        agent_id: str | None = None,
        model: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Query usage records with filters. Returns {records, total}."""
        records: list[dict] = []
        total = 0

        for rec in self._iter_records(date_from, date_to):
            if agent_id and rec.get("agent_id") != agent_id:
                continue
            if model and rec.get("model") != model:
                continue
            total += 1
            if total > offset and len(records) < limit:
                records.append(rec)

        return {"records": records, "total": total, "limit": limit, "offset": offset}

    def summary(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict[str, Any]:
        """Aggregated summary: totals, by_model, by_agent."""
        total_cost = 0.0
        total_tokens = 0
        total_requests = 0
        by_model: dict[str, dict] = {}
        by_agent: dict[str, dict] = {}

        for rec in self._iter_records(date_from, date_to):
            cost = rec.get("cost", 0.0)
            tokens = rec.get("total_tokens", 0)
            m = rec.get("model", "unknown")
            a = rec.get("agent_id", "unknown")

            total_cost += cost
            total_tokens += tokens
            total_requests += 1

            if m not in by_model:
                by_model[m] = {"cost": 0.0, "tokens": 0, "count": 0}
            by_model[m]["cost"] += cost
            by_model[m]["tokens"] += tokens
            by_model[m]["count"] += 1

            if a not in by_agent:
                by_agent[a] = {"cost": 0.0, "tokens": 0, "count": 0}
            by_agent[a]["cost"] += cost
            by_agent[a]["tokens"] += tokens
            by_agent[a]["count"] += 1

        return {
            "total_cost": round(total_cost, 6),
            "total_tokens": total_tokens,
            "total_requests": total_requests,
            "by_model": {
                k: {**v, "cost": round(v["cost"], 6)}
                for k, v in sorted(by_model.items(), key=lambda x: -x[1]["cost"])
            },
            "by_agent": {
                k: {**v, "cost": round(v["cost"], 6)}
                for k, v in sorted(by_agent.items(), key=lambda x: -x[1]["cost"])
            },
        }

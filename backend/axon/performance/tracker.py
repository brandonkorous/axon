"""Performance tracker — records and analyzes agent effectiveness."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from axon.logging import get_logger
from axon.performance.models import AgentRetro, PerformanceMetric

if TYPE_CHECKING:
    from axon.vault.vault import VaultManager

logger = get_logger(__name__)


def _current_week() -> str:
    """Return ISO week string like '2026-W13'."""
    d = date.today()
    return f"{d.isocalendar().year}-W{d.isocalendar().week:02d}"


def _current_month() -> str:
    """Return month string like '2026-03'."""
    d = date.today()
    return f"{d.year}-{d.month:02d}"


class PerformanceTracker:
    """Records and analyzes agent performance metrics.

    Metrics are stored in the shared vault under performance/ as markdown
    files with YAML frontmatter, consistent with the vault-as-database pattern.
    """

    def __init__(self, shared_vault: "VaultManager"):
        self.vault = shared_vault
        self._ensure_branch()

    def _ensure_branch(self) -> None:
        """Ensure the performance/ branch exists."""
        perf_dir = Path(self.vault.vault_path) / "performance"
        perf_dir.mkdir(exist_ok=True)
        index_path = perf_dir / "performance-index.md"
        if not index_path.exists():
            index_path.write_text(
                "---\nname: Performance Index\n"
                "description: Agent performance metrics and retrospectives\n"
                "type: index\n---\n\n"
                "# Performance Tracking\n\n"
                "Agent effectiveness metrics, updated automatically.\n",
                encoding="utf-8",
            )

    def record_recommendation(
        self, agent_id: str, content_summary: str, confidence: float = 0.5,
    ) -> None:
        """Record that an agent made a recommendation."""
        period = _current_week()
        metrics = self._load_or_create_metrics(agent_id, period)
        metrics.recommendations_made += 1
        # Running average of confidence
        n = metrics.recommendations_made
        metrics.avg_confidence = (
            (metrics.avg_confidence * (n - 1) + confidence) / n
        )
        self._save_metrics(metrics)

    def record_outcome(
        self,
        agent_id: str,
        positive: bool,
        recommendation_adopted: bool = True,
    ) -> None:
        """Record the outcome of a recommendation."""
        period = _current_week()
        metrics = self._load_or_create_metrics(agent_id, period)
        metrics.outcomes_tracked += 1
        if positive:
            metrics.positive_outcomes += 1
        if recommendation_adopted:
            metrics.recommendations_adopted += 1
        self._save_metrics(metrics)

    def get_metrics(self, agent_id: str, period: str = "") -> PerformanceMetric:
        """Get metrics for an agent in a given period."""
        if not period:
            period = _current_week()
        return self._load_or_create_metrics(agent_id, period)

    def get_all_metrics(self, agent_id: str, limit: int = 12) -> list[PerformanceMetric]:
        """Get recent metrics for an agent across multiple periods."""
        perf_dir = Path(self.vault.vault_path) / "performance"
        metrics: list[PerformanceMetric] = []

        pattern = f"{agent_id}-*.md"
        files = sorted(perf_dir.glob(pattern), reverse=True)

        for f in files[:limit]:
            try:
                text = f.read_text(encoding="utf-8")
                # Parse YAML frontmatter
                if text.startswith("---"):
                    parts = text.split("---", 2)
                    if len(parts) >= 3:
                        data = yaml.safe_load(parts[1])
                        if data and "agent_id" in data:
                            metrics.append(PerformanceMetric(**data))
            except Exception:
                continue

        return metrics

    def generate_retro(
        self, agent_id: str, agent_name: str = "", period: str = "",
    ) -> AgentRetro:
        """Generate a retrospective analysis for an agent."""
        if not period:
            period = _current_week()

        metrics = self._load_or_create_metrics(agent_id, period)
        insights: list[str] = []
        improvements: list[str] = []

        if metrics.recommendations_made > 0:
            rate = metrics.adoption_rate
            if rate > 0.8:
                insights.append(f"High adoption rate ({rate:.0%}) — recommendations are landing well")
            elif rate < 0.3:
                improvements.append(f"Low adoption rate ({rate:.0%}) — recommendations may not be actionable enough")

        if metrics.outcomes_tracked > 0:
            pos_rate = metrics.positive_outcome_rate
            if pos_rate > 0.7:
                insights.append(f"Strong positive outcome rate ({pos_rate:.0%})")
            elif pos_rate < 0.4:
                improvements.append(f"Low positive outcome rate ({pos_rate:.0%}) — review recommendation quality")

        if metrics.avg_confidence > 0.8:
            insights.append("Consistently high confidence — consider if exploration mode would surface more insights")
        elif metrics.avg_confidence < 0.4:
            improvements.append("Low average confidence — may need more domain context or data")

        return AgentRetro(
            agent_id=agent_id,
            agent_name=agent_name,
            period=period,
            metrics=metrics,
            insights=insights,
            improvement_areas=improvements,
        )

    def _metrics_path(self, agent_id: str, period: str) -> Path:
        return Path(self.vault.vault_path) / "performance" / f"{agent_id}-{period}.md"

    def _load_or_create_metrics(
        self, agent_id: str, period: str,
    ) -> PerformanceMetric:
        """Load existing metrics or create new ones."""
        path = self._metrics_path(agent_id, period)
        if path.exists():
            try:
                text = path.read_text(encoding="utf-8")
                if text.startswith("---"):
                    parts = text.split("---", 2)
                    if len(parts) >= 3:
                        data = yaml.safe_load(parts[1])
                        if data:
                            return PerformanceMetric(**data)
            except Exception:
                pass
        return PerformanceMetric(agent_id=agent_id, period=period)

    def _save_metrics(self, metrics: PerformanceMetric) -> None:
        """Persist metrics to vault as markdown with frontmatter."""
        path = self._metrics_path(metrics.agent_id, metrics.period)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = metrics.model_dump()
        frontmatter = yaml.dump(data, default_flow_style=False, sort_keys=False)

        content = (
            f"---\n{frontmatter}---\n\n"
            f"# {metrics.agent_id} — {metrics.period}\n\n"
            f"- Recommendations: {metrics.recommendations_made}\n"
            f"- Adopted: {metrics.recommendations_adopted}\n"
            f"- Outcomes tracked: {metrics.outcomes_tracked}\n"
            f"- Positive outcomes: {metrics.positive_outcomes}\n"
            f"- Avg confidence: {metrics.avg_confidence:.2f}\n"
        )
        path.write_text(content, encoding="utf-8")

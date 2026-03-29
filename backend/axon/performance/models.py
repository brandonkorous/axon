"""Performance tracking models — agent effectiveness metrics over time."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel


class PerformanceMetric(BaseModel):
    """Aggregated performance metrics for an agent over a time period."""

    agent_id: str
    period: str  # "2026-W13", "2026-03", etc.
    recommendations_made: int = 0
    recommendations_adopted: int = 0
    outcomes_tracked: int = 0
    positive_outcomes: int = 0
    avg_confidence: float = 0.0
    disagreement_rate: float = 0.0  # how often this agent was the dissenting voice
    accuracy_score: float = 0.0  # outcomes that matched predictions

    @property
    def adoption_rate(self) -> float:
        if self.recommendations_made == 0:
            return 0.0
        return self.recommendations_adopted / self.recommendations_made

    @property
    def positive_outcome_rate(self) -> float:
        if self.outcomes_tracked == 0:
            return 0.0
        return self.positive_outcomes / self.outcomes_tracked


class AgentRetro(BaseModel):
    """A retrospective analysis of agent performance."""

    agent_id: str
    agent_name: str = ""
    period: str
    metrics: PerformanceMetric
    insights: list[str] = []
    improvement_areas: list[str] = []
    generated_at: str = ""

    def model_post_init(self, __context: Any) -> None:
        if not self.generated_at:
            self.generated_at = datetime.now(timezone.utc).isoformat()

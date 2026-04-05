"""Self-regulation heuristic — quantified stopping mechanism for agent loops.

Tracks cumulative risk during automated action sequences. When risk exceeds
a threshold, the agent stops and asks the user for confirmation before
continuing. Prevents agents from spiraling through fix/revert loops.
"""

from __future__ import annotations

from pydantic import BaseModel

from axon.logging import get_logger

logger = get_logger(__name__)


class SelfRegulationConfig(BaseModel):
    """Per-agent self-regulation configuration (in agent.yaml)."""

    enabled: bool = False
    wtf_threshold: float = 0.7  # cumulative risk that triggers stop
    risk_per_action: float = 0.1  # default risk per tool call
    risk_per_revert: float = 0.15  # risk added when an action is reverted
    risk_per_large_change: float = 0.05  # risk for changes touching >3 areas
    risk_per_unrelated: float = 0.20  # risk for changes to unrelated files
    max_actions: int = 50  # hard cap on total actions before forced stop


class SelfRegulationTracker:
    """Runtime tracker for cumulative risk during agent processing.

    Usage:
        tracker = SelfRegulationTracker(config)
        should_stop = tracker.record_action()  # True if threshold exceeded
        tracker.record_revert()  # after a reverted action
        tracker.reset()  # after user confirms continuation
    """

    def __init__(self, config: SelfRegulationConfig):
        self._config = config
        self._cumulative_risk: float = 0.0
        self._action_count: int = 0

    @property
    def cumulative_risk(self) -> float:
        return self._cumulative_risk

    @property
    def action_count(self) -> int:
        return self._action_count

    @property
    def should_stop(self) -> bool:
        return (
            self._cumulative_risk >= self._config.wtf_threshold
            or self._action_count >= self._config.max_actions
        )

    def record_action(self, risk: float | None = None) -> bool:
        """Record an action and return True if the agent should stop.

        Args:
            risk: Custom risk value. If None, uses config default.

        Returns:
            True if cumulative risk exceeds threshold or action cap hit.
        """
        actual_risk = risk if risk is not None else self._config.risk_per_action
        self._cumulative_risk += actual_risk
        self._action_count += 1

        if self.should_stop:
            logger.info(
                "Self-regulation triggered: risk=%.2f (threshold=%.2f), actions=%d",
                self._cumulative_risk, self._config.wtf_threshold,
                self._action_count,
            )
            return True
        return False

    def record_revert(self) -> bool:
        """Record a reverted action (higher risk). Returns True if should stop."""
        return self.record_action(self._config.risk_per_revert)

    def record_large_change(self) -> bool:
        """Record a change touching multiple areas. Returns True if should stop."""
        return self.record_action(self._config.risk_per_large_change)

    def record_unrelated_change(self) -> bool:
        """Record a change to unrelated files. Returns True if should stop."""
        return self.record_action(self._config.risk_per_unrelated)

    def reset(self) -> None:
        """Reset after user confirms continuation."""
        self._cumulative_risk = 0.0
        self._action_count = 0
        logger.debug("Self-regulation tracker reset")

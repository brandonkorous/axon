"""Agent lifecycle controls — pause, resume, disable, terminate, strategy override, rate limiting."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class AgentStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    TERMINATED = "terminated"


@dataclass
class RateLimit:
    max_per_minute: int = 10
    window_start: float = 0.0
    count: int = 0

    def check(self) -> bool:
        """Return True if request is allowed, False if rate-limited."""
        now = time.time()
        if now - self.window_start > 60:
            self.window_start = now
            self.count = 0
        if self.count >= self.max_per_minute:
            return False
        self.count += 1
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_per_minute": self.max_per_minute,
            "window_start": self.window_start,
            "count": self.count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> RateLimit:
        return cls(
            max_per_minute=data.get("max_per_minute", 10),
            window_start=data.get("window_start", 0.0),
            count=data.get("count", 0),
        )


@dataclass
class AgentLifecycle:
    """State machine for agent lifecycle management.

    States:
    - active: Normal operation
    - paused: Messages queued, not processed. Resume drains queue.
    - disabled: Messages rejected with error.
    - terminated: Archived. Cannot be restarted.
    """

    agent_id: str
    status: AgentStatus = AgentStatus.ACTIVE
    strategy_override: str | None = None
    rate_limit: RateLimit = field(default_factory=RateLimit)
    paused_at: float | None = None
    terminated_at: float | None = None
    message_queue: list[str] = field(default_factory=list)
    _state_dir: Path | None = None

    def __post_init__(self):
        if self._state_dir:
            self._load()

    @classmethod
    def load(cls, agent_id: str, state_dir: str | Path) -> AgentLifecycle:
        """Load or create lifecycle state for an agent."""
        state_dir = Path(state_dir)
        lc = cls(agent_id=agent_id, _state_dir=state_dir)
        return lc

    # ── State transitions ────────────────────────────────────────────

    def pause(self) -> str:
        if self.status == AgentStatus.TERMINATED:
            return "Cannot pause a terminated agent."
        self.status = AgentStatus.PAUSED
        self.paused_at = time.time()
        self._save()
        return "Agent paused. Messages will be queued."

    def resume(self) -> tuple[str, list[str]]:
        """Resume the agent, returning any queued messages."""
        if self.status != AgentStatus.PAUSED:
            return "Agent is not paused.", []
        queued = list(self.message_queue)
        self.message_queue.clear()
        self.status = AgentStatus.ACTIVE
        self.paused_at = None
        self._save()
        return f"Agent resumed. {len(queued)} queued message(s).", queued

    def disable(self) -> str:
        if self.status == AgentStatus.TERMINATED:
            return "Cannot disable a terminated agent."
        self.status = AgentStatus.DISABLED
        self._save()
        return "Agent disabled. Messages will be rejected."

    def enable(self) -> str:
        if self.status == AgentStatus.TERMINATED:
            return "Cannot enable a terminated agent."
        self.status = AgentStatus.ACTIVE
        self._save()
        return "Agent enabled."

    def terminate(self) -> str:
        self.status = AgentStatus.TERMINATED
        self.terminated_at = time.time()
        self.message_queue.clear()
        self._save()
        return "Agent terminated. This is irreversible."

    # ── Strategy override ────────────────────────────────────────────

    def set_strategy_override(self, prompt: str) -> str:
        self.strategy_override = prompt
        self._save()
        return f"Strategy override set: {prompt[:100]}..."

    def clear_strategy_override(self) -> str:
        self.strategy_override = None
        self._save()
        return "Strategy override cleared."

    # ── Rate limiting ────────────────────────────────────────────────

    def set_rate_limit(self, max_per_minute: int) -> str:
        self.rate_limit.max_per_minute = max_per_minute
        self._save()
        return f"Rate limit set to {max_per_minute}/min."

    # ── Message handling check ───────────────────────────────────────

    def check_message(self, message: str) -> tuple[str, bool]:
        """Check if a message can be processed.

        Returns (status_message, can_process).
        If paused, the message is queued.
        """
        if self.status == AgentStatus.TERMINATED:
            return "Agent has been terminated.", False

        if self.status == AgentStatus.DISABLED:
            return "Agent is currently disabled.", False

        if self.status == AgentStatus.PAUSED:
            self.message_queue.append(message)
            self._save()
            return f"Agent is paused. Message queued (position {len(self.message_queue)}).", False

        if not self.rate_limit.check():
            return "Rate limit exceeded. Try again in a moment.", False

        return "ok", True

    # ── Serialization ────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "status": self.status.value,
            "strategy_override": self.strategy_override,
            "rate_limit": self.rate_limit.to_dict(),
            "paused_at": self.paused_at,
            "terminated_at": self.terminated_at,
            "queued_messages": len(self.message_queue),
        }

    def _state_path(self) -> Path | None:
        if not self._state_dir:
            return None
        self._state_dir.mkdir(parents=True, exist_ok=True)
        return self._state_dir / f"{self.agent_id}.json"

    def _save(self) -> None:
        path = self._state_path()
        if not path:
            return
        data = {
            "status": self.status.value,
            "strategy_override": self.strategy_override,
            "rate_limit": self.rate_limit.to_dict(),
            "paused_at": self.paused_at,
            "terminated_at": self.terminated_at,
            "message_queue": self.message_queue,
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _load(self) -> None:
        path = self._state_path()
        if not path or not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            self.status = AgentStatus(data.get("status", "active"))
            self.strategy_override = data.get("strategy_override")
            self.rate_limit = RateLimit.from_dict(data.get("rate_limit", {}))
            self.paused_at = data.get("paused_at")
            self.terminated_at = data.get("terminated_at")
            self.message_queue = data.get("message_queue", [])
        except Exception:
            pass  # Start fresh if state file is corrupted

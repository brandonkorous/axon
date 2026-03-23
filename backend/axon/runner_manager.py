"""RunnerManager — file-based runner state management.

The backend writes state.json files to signal desired state.
A host-side runner service (runner_host.py) watches these files
and manages the actual subprocess lifecycle on the host machine
where Claude CLI and codebases are accessible.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from axon.config import settings

logger = logging.getLogger(__name__)


class RunnerManager:
    """Manages runner desired-state via the shared orgs filesystem."""

    @staticmethod
    def _runner_dir(org_id: str, agent_id: str) -> Path:
        return Path(settings.axon_orgs_dir) / org_id / "runners" / agent_id

    @staticmethod
    def _write_state(runner_dir: Path, state: str) -> None:
        state_path = runner_dir / "state.json"
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump({"state": state}, f)

    @staticmethod
    def _read_status(runner_dir: Path) -> str:
        """Read actual status written by the host runner service."""
        status_path = runner_dir / "status.json"
        try:
            with open(status_path, encoding="utf-8") as f:
                return json.load(f).get("status", "stopped")
        except (FileNotFoundError, json.JSONDecodeError):
            return "stopped"

    # ── Lifecycle (writes desired state for host service) ──────────

    async def start(self, org_id: str, agent_id: str) -> None:
        runner_dir = self._runner_dir(org_id, agent_id)
        if not (runner_dir / "runner.js").exists():
            raise FileNotFoundError(f"Runner not scaffolded: {runner_dir}")
        self._write_state(runner_dir, "running")
        logger.info("Requested start for %s/%s", org_id, agent_id)

    async def stop(self, org_id: str, agent_id: str) -> None:
        runner_dir = self._runner_dir(org_id, agent_id)
        self._write_state(runner_dir, "stop")
        logger.info("Requested stop for %s/%s", org_id, agent_id)

    async def pause(self, org_id: str, agent_id: str) -> None:
        runner_dir = self._runner_dir(org_id, agent_id)
        self._write_state(runner_dir, "paused")
        logger.info("Requested pause for %s/%s", org_id, agent_id)

    async def resume(self, org_id: str, agent_id: str) -> None:
        runner_dir = self._runner_dir(org_id, agent_id)
        self._write_state(runner_dir, "running")
        logger.info("Requested resume for %s/%s", org_id, agent_id)

    # ── Status & logs ──────────────────────────────────────────────

    def status(self, org_id: str, agent_id: str) -> str:
        """Read actual status from status.json (written by host service)."""
        runner_dir = self._runner_dir(org_id, agent_id)
        return self._read_status(runner_dir)

    def get_logs(self, org_id: str, agent_id: str, lines: int = 100) -> list[str]:
        log_path = self._runner_dir(org_id, agent_id) / "runner.log"
        if not log_path.exists():
            return []
        return _tail(log_path, lines)

    # ── Shutdown / cleanup ─────────────────────────────────────────

    async def shutdown_all(self) -> None:
        """Signal all runners to stop (host service handles actual shutdown)."""
        orgs_dir = Path(settings.axon_orgs_dir)
        if not orgs_dir.exists():
            return
        count = 0
        for org_dir in orgs_dir.iterdir():
            runners_dir = org_dir / "runners"
            if not runners_dir.is_dir():
                continue
            for runner_dir in runners_dir.iterdir():
                status = self._read_status(runner_dir)
                if status in ("running", "paused"):
                    self._write_state(runner_dir, "stop")
                    count += 1
        if count:
            logger.info("Signaled %d runner(s) to stop", count)

    def cleanup_stale_pids(self) -> None:
        """Reset state files on backend startup."""
        orgs_dir = Path(settings.axon_orgs_dir)
        if not orgs_dir.exists():
            return
        for org_dir in orgs_dir.iterdir():
            runners_dir = org_dir / "runners"
            if not runners_dir.is_dir():
                continue
            for runner_dir in runners_dir.iterdir():
                pid_file = runner_dir / "runner.pid"
                if pid_file.exists():
                    pid_file.unlink(missing_ok=True)


# ── Helpers ──────────────────────────────────────────────────────

def _tail(path: Path, n: int) -> list[str]:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
        return [line.rstrip("\n") for line in all_lines[-n:]]
    except Exception:
        return []


# Singleton
runner_manager = RunnerManager()

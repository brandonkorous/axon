"""AgentScheduler — APScheduler-based heartbeat for proactive agent behaviors.

Uses APScheduler 3.x AsyncIOScheduler for interval-based job scheduling.
Domain logic (what happens when a job fires) lives in scheduler_jobs.py.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from axon.logging import get_logger
from axon.scheduler_jobs import (
    fire_memory_consolidation,
    fire_proactive_check,
    fire_review_done,
    fire_task_work,
    find_agent_tasks,
)

if TYPE_CHECKING:
    from axon.agents.agent import Agent

logger = get_logger(__name__)

# Interval durations (seconds)
INTERVAL_SECONDS = {
    "frequent": 120,
    "hourly": 3600,
    "daily": 86400,
    "weekly": 604800,
}

# Jitter (seconds) to avoid thundering herd when many agents share an interval
JITTER = 10


class AgentScheduler:
    """Manages per-agent scheduled jobs via APScheduler."""

    def __init__(self) -> None:
        self._scheduler = AsyncIOScheduler(
            job_defaults={
                "coalesce": True,
                "max_instances": 1,
                "misfire_grace_time": 60,
            },
        )
        self._in_flight_tasks: set[str] = set()

    def start(self) -> None:
        """Start the APScheduler event loop."""
        if self._scheduler.running:
            return
        self._scheduler.start()
        self._register_all_agents()
        logger.info("scheduler_started")

    async def stop(self) -> None:
        """Shut down the scheduler gracefully."""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
        logger.info("scheduler_stopped")

    # ── Dynamic agent management ────────────────────────────────

    def register_agent(self, org_id: str, agent_id: str, agent: "Agent") -> None:
        """Add scheduled jobs for a newly created agent."""
        self._add_agent_jobs(org_id, agent_id, agent)
        logger.info("agent_registered", org_id=org_id, agent_id=agent_id)

    def unregister_agent(self, org_id: str, agent_id: str) -> None:
        """Remove all scheduled jobs for a departing agent."""
        prefix = f"{org_id}:{agent_id}:"
        for job in self._scheduler.get_jobs():
            if job.id.startswith(prefix):
                job.remove()
        logger.info("agent_unregistered", org_id=org_id, agent_id=agent_id)

    # ── Immediate triggers ──────────────────────────────────────

    async def trigger_task_execution(self, org_id: str, agent_id: str) -> None:
        """Immediately trigger task execution for a specific agent."""
        import axon.registry as registry

        org = registry.org_registry.get(org_id)
        if not org:
            logger.warning("trigger_task_org_not_found", org_id=org_id)
            return

        agent = org.agent_registry.get(agent_id)
        if not agent:
            logger.warning("trigger_task_agent_not_found", agent_id=agent_id)
            return

        logger.info("trigger_task_immediate", org_id=org_id, agent_id=agent_id)
        await fire_task_work(org_id, agent_id, agent, self._in_flight_tasks)

    # ── Internal ────────────────────────────────────────────────

    def _register_all_agents(self) -> None:
        """Scan all orgs/agents and register their jobs."""
        import axon.registry as registry

        for org_id, org in registry.org_registry.items():
            for agent_id, agent in org.agent_registry.items():
                self._add_agent_jobs(org_id, agent_id, agent)

    def _add_agent_jobs(self, org_id: str, agent_id: str, agent: "Agent") -> None:
        """Register APScheduler jobs for a single agent."""
        # Task work (every 2 minutes) — only if agent has a shared vault
        if agent.shared_vault:
            self._scheduler.add_job(
                self._job_task_work,
                trigger=IntervalTrigger(seconds=INTERVAL_SECONDS["frequent"], jitter=JITTER),
                id=f"{org_id}:{agent_id}:work_on_tasks",
                args=[org_id, agent_id],
                replace_existing=True,
            )

            # Review done tasks (every 2 minutes)
            self._scheduler.add_job(
                self._job_review_done,
                trigger=IntervalTrigger(seconds=INTERVAL_SECONDS["frequent"], jitter=JITTER),
                id=f"{org_id}:{agent_id}:review_done",
                args=[org_id, agent_id],
                replace_existing=True,
            )

        # Custom proactive checks from agent config
        checks = agent.config.behavior.proactive_checks
        for check in checks:
            if check.action == "work_on_tasks":
                continue  # Handled above

            interval = INTERVAL_SECONDS.get(check.trigger, INTERVAL_SECONDS["daily"])

            if check.action == "consolidate_memory":
                self._scheduler.add_job(
                    self._job_memory_consolidation,
                    trigger=IntervalTrigger(seconds=interval, jitter=JITTER),
                    id=f"{org_id}:{agent_id}:{check.action}",
                    args=[org_id, agent_id],
                    replace_existing=True,
                )
            else:
                self._scheduler.add_job(
                    self._job_proactive_check,
                    trigger=IntervalTrigger(seconds=interval, jitter=JITTER),
                    id=f"{org_id}:{agent_id}:{check.action}",
                    args=[org_id, agent_id, check.action, check.description],
                    replace_existing=True,
                )

    # ── Job wrappers (resolve agent at execution time) ──────────

    async def _job_task_work(self, org_id: str, agent_id: str) -> None:
        agent = self._resolve_agent(org_id, agent_id)
        if agent:
            await fire_task_work(org_id, agent_id, agent, self._in_flight_tasks)

    async def _job_review_done(self, org_id: str, agent_id: str) -> None:
        agent = self._resolve_agent(org_id, agent_id)
        if agent:
            await fire_review_done(org_id, agent_id, agent)

    async def _job_memory_consolidation(self, org_id: str, agent_id: str) -> None:
        agent = self._resolve_agent(org_id, agent_id)
        if agent:
            await fire_memory_consolidation(org_id, agent_id, agent)

    async def _job_proactive_check(
        self, org_id: str, agent_id: str, action: str, description: str,
    ) -> None:
        agent = self._resolve_agent(org_id, agent_id)
        if agent:
            await fire_proactive_check(org_id, agent_id, agent, action, description)

    @staticmethod
    def _resolve_agent(org_id: str, agent_id: str) -> "Agent | None":
        """Look up an agent from the registry (may have been deleted)."""
        import axon.registry as registry

        org = registry.org_registry.get(org_id)
        if not org:
            return None
        return org.agent_registry.get(agent_id)


# Singleton
scheduler = AgentScheduler()

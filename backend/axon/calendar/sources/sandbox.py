"""Sandbox event source — shows currently active sandbox sessions."""

from __future__ import annotations

import logging
from datetime import datetime

from axon.calendar.types import CalendarEvent, CalendarEventSource

logger = logging.getLogger(__name__)


class SandboxEventSource(CalendarEventSource):
    """Produces events for currently running sandboxes."""

    source_name = "sandbox"

    async def get_events(
        self,
        org_id: str,
        start: str,
        end: str,
        agent_filter: str | None = None,
    ) -> list[CalendarEvent]:
        from axon.sandbox.manager import sandbox_manager
        import axon.registry as registry

        today = datetime.now().strftime("%Y-%m-%d")
        if today < start or today > end:
            return []

        org = registry.org_registry.get(org_id)
        if not org:
            return []

        agent_colors: dict[str, dict[str, str]] = {}
        for aid, agent in org.agent_registry.items():
            agent_colors[aid] = {
                "name": agent.config.name,
                "color": agent.config.ui.color,
            }

        events: list[CalendarEvent] = []
        prefix = f"{org_id}/"

        for key, sandbox_id in sandbox_manager._containers.items():
            if not key.startswith(prefix):
                continue
            parts = key.split("/", 2)
            if len(parts) < 3:
                continue
            agent_id = parts[1]
            instance_id = parts[2]

            if agent_filter and agent_id != agent_filter:
                continue

            info = agent_colors.get(agent_id, {})
            events.append(
                CalendarEvent(
                    id=f"sandbox::{key}",
                    title=f"Sandbox: {agent_id}/{instance_id}",
                    start_date=today,
                    source="sandbox",
                    agent_id=agent_id,
                    agent_name=info.get("name"),
                    agent_color=info.get("color"),
                    status="running",
                    metadata={
                        "instance_id": instance_id,
                        "sandbox_id": sandbox_id[:12],
                    },
                )
            )

        return events

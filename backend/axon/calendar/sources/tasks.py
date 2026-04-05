"""Task event source — converts vault tasks into calendar events."""

from __future__ import annotations

from datetime import datetime, timedelta
from math import ceil

from axon.calendar.types import CalendarEvent, CalendarEventSource
from axon.logging import get_logger

logger = get_logger(__name__)


class TaskEventSource(CalendarEventSource):
    """Produces calendar events from tasks in the shared vault."""

    source_name = "task"

    async def get_events(
        self,
        org_id: str,
        start: str,
        end: str,
        agent_filter: str | None = None,
    ) -> list[CalendarEvent]:
        from axon.routes.tasks import _get_shared_vault, _parse_tasks

        try:
            vault = _get_shared_vault(org_id)
        except Exception:
            return []

        tasks = _parse_tasks(vault)
        agent_colors = _get_agent_colors(org_id)
        events: list[CalendarEvent] = []

        for task in tasks:
            task_start = task.get("start_date") or ""
            task_due = task.get("due_date") or ""
            estimated = task.get("estimated_hours")

            if not task_start and not task_due:
                continue

            assignee = task.get("assignee") or ""
            if agent_filter and assignee != agent_filter:
                continue

            # Determine event date range
            event_start = task_start or task_due
            event_end: str | None = None

            if task_start and task_due and task_start != task_due:
                event_end = task_due
            elif task_start and estimated:
                days = max(1, ceil(estimated / 8))
                try:
                    dt = datetime.strptime(task_start, "%Y-%m-%d")
                    event_end = (dt + timedelta(days=days - 1)).strftime("%Y-%m-%d")
                except ValueError:
                    pass

            # Skip if entirely outside the requested range
            latest_date = event_end or event_start
            if latest_date < start or event_start > end:
                continue

            color_info = agent_colors.get(assignee, {})
            events.append(
                CalendarEvent(
                    id=f"task::{task.get('path', '')}",
                    title=task.get("name", "Untitled"),
                    start_date=event_start,
                    end_date=event_end,
                    source="task",
                    agent_id=assignee or None,
                    agent_name=color_info.get("name"),
                    agent_color=color_info.get("color"),
                    status=task.get("status"),
                    priority=task.get("priority"),
                    metadata={
                        "path": task.get("path", ""),
                        "owner": task.get("owner", ""),
                        "labels": task.get("labels", []),
                        "estimated_hours": estimated,
                    },
                )
            )

        return events


def _get_agent_colors(org_id: str) -> dict[str, dict[str, str]]:
    """Build a lookup of agent_id -> {name, color} for the org."""
    import axon.registry as registry

    org = registry.org_registry.get(org_id)
    if not org:
        return {}
    result: dict[str, dict[str, str]] = {}
    for agent_id, agent in org.agent_registry.items():
        result[agent_id] = {
            "name": agent.config.name,
            "color": agent.config.ui.color,
        }
    return result

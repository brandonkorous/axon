"""Scheduler event source — shows agent proactive check patterns."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from axon.calendar.types import CalendarEvent, CalendarEventSource
from axon.scheduler import INTERVAL_SECONDS

logger = logging.getLogger(__name__)

# Human-readable labels for intervals
INTERVAL_LABELS = {
    "frequent": "Every 2m",
    "hourly": "Hourly",
    "daily": "Daily",
    "weekly": "Weekly",
}


class SchedulerEventSource(CalendarEventSource):
    """Produces day-level markers for agent proactive checks."""

    source_name = "scheduled_action"

    async def get_events(
        self,
        org_id: str,
        start: str,
        end: str,
        agent_filter: str | None = None,
    ) -> list[CalendarEvent]:
        import axon.registry as registry

        org = registry.org_registry.get(org_id)
        if not org:
            return []

        events: list[CalendarEvent] = []
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d")

        for agent_id, agent in org.agent_registry.items():
            if agent_filter and agent_id != agent_filter:
                continue

            checks = agent.config.behavior.proactive_checks
            if not checks:
                continue

            color = agent.config.ui.color
            name = agent.config.name

            for check in checks:
                interval = check.trigger
                interval_secs = INTERVAL_SECONDS.get(interval, 86400)

                # For frequent/hourly checks, show one marker per day
                # For daily, one per day. For weekly, one per week.
                if interval_secs >= 604800:  # weekly
                    # One event per week in range
                    day = start_dt
                    week_num = 0
                    while day <= end_dt:
                        events.append(
                            _make_event(
                                agent_id, name, color, check, day, interval,
                            )
                        )
                        day += timedelta(days=7)
                        week_num += 1
                else:
                    # One event per day in range
                    day = start_dt
                    while day <= end_dt:
                        events.append(
                            _make_event(
                                agent_id, name, color, check, day, interval,
                            )
                        )
                        day += timedelta(days=1)

        return events


def _make_event(
    agent_id: str,
    agent_name: str,
    agent_color: str,
    check,
    day: datetime,
    interval: str,
) -> CalendarEvent:
    date_str = day.strftime("%Y-%m-%d")
    label = INTERVAL_LABELS.get(interval, interval)
    title = f"{check.action} ({label})"

    return CalendarEvent(
        id=f"schedule::{agent_id}:{check.action}:{date_str}",
        title=title,
        start_date=date_str,
        source="scheduled_action",
        agent_id=agent_id,
        agent_name=agent_name,
        agent_color=agent_color,
        metadata={
            "action": check.action,
            "description": check.description,
            "interval": interval,
        },
    )

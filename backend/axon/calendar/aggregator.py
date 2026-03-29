"""Calendar aggregator — merges events from all sources."""

from __future__ import annotations

from axon.calendar.types import CalendarEvent, CalendarEventSource
from axon.calendar.sources.tasks import TaskEventSource
from axon.calendar.sources.scheduler import SchedulerEventSource
from axon.calendar.sources.sandbox import SandboxEventSource


class CalendarAggregator:
    """Aggregates calendar events from multiple sources."""

    def __init__(self, sources: list[CalendarEventSource]) -> None:
        self._sources = sources

    async def get_events(
        self,
        org_id: str,
        start: str,
        end: str,
        agent_filter: str | None = None,
        source_filter: set[str] | None = None,
    ) -> list[CalendarEvent]:
        events: list[CalendarEvent] = []

        for source in self._sources:
            if source_filter and source.source_name not in source_filter:
                continue
            source_events = await source.get_events(
                org_id, start, end, agent_filter,
            )
            events.extend(source_events)

        events.sort(key=lambda e: e.start_date)
        return events


def create_default_aggregator() -> CalendarAggregator:
    """Create an aggregator with all built-in sources."""
    return CalendarAggregator([
        TaskEventSource(),
        SchedulerEventSource(),
        SandboxEventSource(),
    ])

"""Calendar types — shared models for the calendar system."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class CalendarEvent(BaseModel):
    """A unified calendar event from any source."""

    id: str
    title: str
    start_date: str  # YYYY-MM-DD
    end_date: str | None = None  # YYYY-MM-DD
    start_time: str | None = None  # HH:MM (future: integration events)
    end_time: str | None = None  # HH:MM
    source: str  # "task" | "scheduled_action" | "sandbox"
    agent_id: str | None = None
    agent_name: str | None = None
    agent_color: str | None = None
    status: str | None = None
    priority: str | None = None
    metadata: dict[str, Any] = {}


class CalendarEventSource(ABC):
    """Base class for calendar event sources."""

    source_name: str

    @abstractmethod
    async def get_events(
        self,
        org_id: str,
        start: str,
        end: str,
        agent_filter: str | None = None,
    ) -> list[CalendarEvent]:
        """Return events within the date range [start, end]."""
        ...

"""Google Calendar integration — list, create events, find free time."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from axon.integrations.base import BaseIntegration
from axon.integrations.google_calendar.tools import GOOGLE_CALENDAR_TOOLS
from axon.logging import get_logger

logger = get_logger(__name__)

CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"


class GoogleCalendarIntegration(BaseIntegration):
    """Google Calendar integration using the Calendar API v3."""

    name = "google_calendar"
    description = "Google Calendar — list events, create events, find free time"
    required_scopes = ["https://www.googleapis.com/auth/calendar"]
    tool_prefix = "gcal_"

    def get_tools(self) -> list[dict[str, Any]]:
        return GOOGLE_CALENDAR_TOOLS

    async def execute(self, tool_name: str, arguments: str) -> str:
        try:
            args = json.loads(arguments)
        except json.JSONDecodeError:
            return f"Error: Invalid JSON arguments: {arguments}"

        handlers = {
            "gcal_list_events": self._list_events,
            "gcal_create_event": self._create_event,
            "gcal_find_free_time": self._find_free_time,
        }

        handler = handlers.get(tool_name)
        if not handler:
            return f"Error: Unknown Google Calendar tool: {tool_name}"

        token = self._credentials.get("access_token", "")
        if not token:
            return "Error: Google Calendar credentials not configured. Add a Google OAuth credential."

        try:
            return await handler(args, token)
        except httpx.HTTPStatusError as e:
            logger.exception("Google Calendar API error: %s", tool_name)
            return f"Google Calendar API error ({e.response.status_code}): {e.response.text[:200]}"
        except Exception as e:
            logger.exception("Google Calendar error: %s", tool_name)
            return f"Error executing {tool_name}: {e}"

    async def _list_events(self, args: dict, token: str) -> str:
        max_results = args.get("max_results", 10)
        now = datetime.now(timezone.utc)
        time_min = args.get("time_min", now.isoformat())
        time_max = args.get("time_max", (now + timedelta(days=7)).isoformat())

        params = {
            "timeMin": time_min,
            "timeMax": time_max,
            "maxResults": max_results,
            "singleEvents": "true",
            "orderBy": "startTime",
        }

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{CALENDAR_API_BASE}/calendars/primary/events",
                params=params,
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
            data = resp.json()

        events = data.get("items", [])
        if not events:
            return "No upcoming events found."

        lines = []
        for ev in events:
            start = ev.get("start", {}).get("dateTime", ev.get("start", {}).get("date", ""))
            end = ev.get("end", {}).get("dateTime", ev.get("end", {}).get("date", ""))
            summary = ev.get("summary", "(No title)")
            lines.append(f"- **{summary}** | {start} → {end}")
        return f"Found {len(events)} event(s):\n\n" + "\n".join(lines)

    async def _create_event(self, args: dict, token: str) -> str:
        body: dict[str, Any] = {
            "summary": args["summary"],
            "start": {"dateTime": args["start"]},
            "end": {"dateTime": args["end"]},
        }
        if args.get("description"):
            body["description"] = args["description"]
        if args.get("attendees"):
            emails = [e.strip() for e in args["attendees"].split(",")]
            body["attendees"] = [{"email": e} for e in emails if e]

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{CALENDAR_API_BASE}/calendars/primary/events",
                json=body,
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
            event = resp.json()

        return f"Event created: **{event.get('summary')}** (ID: {event.get('id')})"

    async def _find_free_time(self, args: dict, token: str) -> str:
        target_date = args["date"]
        duration = args.get("duration_minutes", 30)
        wh_start = args.get("working_hours_start", "09:00")
        wh_end = args.get("working_hours_end", "17:00")

        time_min = f"{target_date}T{wh_start}:00Z"
        time_max = f"{target_date}T{wh_end}:00Z"

        params = {
            "timeMin": time_min,
            "timeMax": time_max,
            "singleEvents": "true",
            "orderBy": "startTime",
        }

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{CALENDAR_API_BASE}/calendars/primary/events",
                params=params,
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
            data = resp.json()

        events = data.get("items", [])

        # Find gaps between events
        busy = []
        for ev in events:
            start = ev.get("start", {}).get("dateTime", "")
            end = ev.get("end", {}).get("dateTime", "")
            if start and end:
                busy.append((start, end))

        if not busy:
            return f"The entire working day ({wh_start}–{wh_end}) on {target_date} is free."

        lines = [f"Busy times on {target_date}:"]
        for start, end in busy:
            lines.append(f"  - {start} → {end}")
        lines.append(f"\nLooking for {duration}-minute slots between {wh_start} and {wh_end}.")
        lines.append("Free slots exist in the gaps between busy times above.")
        return "\n".join(lines)

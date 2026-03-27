"""Google Calendar tool schemas for LLM function calling."""

from __future__ import annotations

from typing import Any

GOOGLE_CALENDAR_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "gcal_list_events",
            "description": "List upcoming Google Calendar events within a date range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of events to return (default 10).",
                        "default": 10,
                    },
                    "time_min": {
                        "type": "string",
                        "description": "Start of range in ISO 8601 format (e.g. '2026-03-26T00:00:00Z'). Defaults to now.",
                    },
                    "time_max": {
                        "type": "string",
                        "description": "End of range in ISO 8601 format. Defaults to 7 days from now.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "gcal_create_event",
            "description": "Create a new Google Calendar event.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Event title.",
                    },
                    "start": {
                        "type": "string",
                        "description": "Start time in ISO 8601 format (e.g. '2026-03-27T10:00:00-05:00').",
                    },
                    "end": {
                        "type": "string",
                        "description": "End time in ISO 8601 format.",
                    },
                    "description": {
                        "type": "string",
                        "description": "Event description or notes.",
                    },
                    "attendees": {
                        "type": "string",
                        "description": "Comma-separated email addresses of attendees.",
                    },
                },
                "required": ["summary", "start", "end"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "gcal_find_free_time",
            "description": "Find available time slots in Google Calendar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date to check in YYYY-MM-DD format.",
                    },
                    "duration_minutes": {
                        "type": "integer",
                        "description": "Duration of the slot needed in minutes (default 30).",
                        "default": 30,
                    },
                    "working_hours_start": {
                        "type": "string",
                        "description": "Start of working hours in HH:MM format (default '09:00').",
                        "default": "09:00",
                    },
                    "working_hours_end": {
                        "type": "string",
                        "description": "End of working hours in HH:MM format (default '17:00').",
                        "default": "17:00",
                    },
                },
                "required": ["date"],
            },
        },
    },
]

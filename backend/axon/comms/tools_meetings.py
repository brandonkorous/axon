"""Meeting and event creation tool schemas for Zoom, Teams, and Discord."""

from __future__ import annotations

from typing import Any

MEETING_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "comms_create_zoom_meeting",
            "description": (
                "Create a Zoom meeting and return the join URL. Use this to schedule "
                "calls, interviews, or meetings on behalf of the user."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Meeting topic/title",
                    },
                    "duration": {
                        "type": "integer",
                        "description": "Meeting duration in minutes (default: 30)",
                    },
                    "start_time": {
                        "type": "string",
                        "description": "ISO 8601 start time (e.g. 2026-03-28T14:00:00Z). Omit for instant meeting.",
                    },
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "comms_create_teams_meeting",
            "description": (
                "Create a Microsoft Teams online meeting and return the join URL. "
                "Use this to schedule calls, interviews, or meetings."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "subject": {
                        "type": "string",
                        "description": "Meeting subject/title",
                    },
                    "duration": {
                        "type": "integer",
                        "description": "Meeting duration in minutes (default: 30)",
                    },
                    "start_time": {
                        "type": "string",
                        "description": "ISO 8601 start time (e.g. 2026-03-28T14:00:00Z). Omit for instant meeting.",
                    },
                },
                "required": ["subject"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "comms_create_discord_event",
            "description": (
                "Create a Discord scheduled event in the server. Use this to schedule "
                "community events, meetings, or gatherings."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Event name/title",
                    },
                    "start_time": {
                        "type": "string",
                        "description": "ISO 8601 start time (e.g. 2026-03-28T14:00:00Z)",
                    },
                    "end_time": {
                        "type": "string",
                        "description": "ISO 8601 end time. Defaults to start_time + 1 hour if omitted.",
                    },
                    "description": {
                        "type": "string",
                        "description": "Event description (optional)",
                    },
                    "location": {
                        "type": "string",
                        "description": "Event location — a URL or place name (default: 'Online')",
                    },
                },
                "required": ["name", "start_time"],
            },
        },
    },
]

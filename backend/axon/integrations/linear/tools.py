"""Linear tool schemas for LLM function calling."""

from __future__ import annotations

from typing import Any

LINEAR_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "linear_list_issues",
            "description": "List Linear issues with optional filters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter by status (e.g. 'In Progress', 'Todo', 'Done').",
                    },
                    "assignee": {
                        "type": "string",
                        "description": "Filter by assignee display name or email.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of issues to return (default 20).",
                        "default": 20,
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "linear_create_issue",
            "description": "Create a new issue in Linear.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Issue title.",
                    },
                    "description": {
                        "type": "string",
                        "description": "Issue description (supports markdown).",
                    },
                    "team_key": {
                        "type": "string",
                        "description": "Team key or name to create the issue in.",
                    },
                    "priority": {
                        "type": "integer",
                        "description": "Priority: 0=None, 1=Urgent, 2=High, 3=Medium, 4=Low.",
                    },
                    "assignee_email": {
                        "type": "string",
                        "description": "Email of the person to assign the issue to.",
                    },
                },
                "required": ["title", "team_key"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "linear_update_issue",
            "description": "Update an existing Linear issue's status or assignee.",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_id": {
                        "type": "string",
                        "description": "The Linear issue ID (e.g. 'ABC-123' or UUID).",
                    },
                    "status": {
                        "type": "string",
                        "description": "New status name (e.g. 'In Progress', 'Done').",
                    },
                    "assignee_email": {
                        "type": "string",
                        "description": "Email of the new assignee.",
                    },
                    "priority": {
                        "type": "integer",
                        "description": "New priority: 0=None, 1=Urgent, 2=High, 3=Medium, 4=Low.",
                    },
                },
                "required": ["issue_id"],
            },
        },
    },
]

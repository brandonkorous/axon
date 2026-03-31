"""Tool schemas for plugin discovery — always available to agents."""

from __future__ import annotations

from typing import Any

CAPABILITY_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "plugins_discover",
            "description": (
                "Search for available plugins, skills, integrations, and sandbox "
                "environments across the organization. Returns matching plugins "
                "with descriptions, whether they're currently enabled for you, and "
                "what they require (credentials, sandbox type). Use this before "
                "requesting access to understand what's available."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Free-text search — describe what you need "
                            "(e.g., 'spreadsheet generation', 'web scraping', 'OCR')"
                        ),
                    },
                    "category": {
                        "type": "string",
                        "description": "Filter by category (e.g., 'research', 'engineering', 'communication')",
                    },
                    "type": {
                        "type": "string",
                        "enum": ["plugin", "skill", "integration", "sandbox"],
                        "description": "Filter to a specific capability type",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "plugins_enable",
            "description": (
                "Request access to an existing plugin (plugin, skill, or "
                "integration) that you found via plugins_discover but don't "
                "currently have enabled. If no credentials are required, it will "
                "be auto-enabled immediately. Otherwise, the request goes to a "
                "human for approval."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["plugin", "skill", "integration"],
                        "description": "Type of capability to enable",
                    },
                    "name": {
                        "type": "string",
                        "description": "Exact name of the plugin (from plugins_discover results)",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Why you need this capability — helps with audit and approval",
                    },
                },
                "required": ["type", "name", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "plugins_request",
            "description": (
                "Request a plugin that doesn't exist yet. Use this when "
                "plugins_discover returned no matches for what you need. "
                "Creates a request that a human can approve and a builder agent "
                "can scaffold into a new plugin or skill."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": (
                            "What capability you need — be specific about the "
                            "functionality (e.g., 'OCR text extraction from images "
                            "and PDFs using Tesseract or similar')"
                        ),
                    },
                    "use_case": {
                        "type": "string",
                        "description": "The concrete task you're trying to accomplish that requires this",
                    },
                    "suggested_tools": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Tool names you'd expect this capability to provide "
                            "(e.g., ['ocr_extract_text', 'ocr_extract_tables'])"
                        ),
                    },
                },
                "required": ["description", "use_case"],
            },
        },
    },
]

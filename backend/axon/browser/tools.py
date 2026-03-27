"""Browser tool schemas — Playwright-based web automation for agents."""

from __future__ import annotations

from typing import Any


BROWSER_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "browser_navigate",
            "description": (
                "Navigate to a URL and extract the page content as structured markdown. "
                "Use this for pages that require JavaScript rendering (SPAs, dynamic content) "
                "where web_fetch returns incomplete results."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to navigate to",
                    },
                    "wait_for": {
                        "type": "string",
                        "description": "CSS selector to wait for before extracting (optional)",
                    },
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_extract",
            "description": (
                "Extract specific content from the current page using a CSS selector. "
                "Returns the text content of all matching elements."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector to extract content from",
                    },
                },
                "required": ["selector"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_screenshot",
            "description": (
                "Take a screenshot of the current page. Returns the screenshot as a "
                "base64-encoded PNG. Useful for visual verification or capturing dynamic content."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "full_page": {
                        "type": "boolean",
                        "description": "Capture full page (true) or just viewport (false, default)",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_click",
            "description": (
                "Click an element on the current page. Use for interacting with buttons, "
                "links, or other clickable elements."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector of the element to click",
                    },
                },
                "required": ["selector"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_fill",
            "description": (
                "Fill a form field on the current page. Use for typing into input fields, "
                "textareas, or other editable elements."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector of the input element",
                    },
                    "value": {
                        "type": "string",
                        "description": "Value to fill in",
                    },
                },
                "required": ["selector", "value"],
            },
        },
    },
]

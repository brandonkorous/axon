"""WEB_TOOLS — tool schemas for web search and content fetching."""

from __future__ import annotations

from typing import Any


WEB_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the web for current information. Returns titles, URLs, "
                "and snippets for the top results. Use this when you need up-to-date "
                "information that isn't in your vault — prices, trends, recommendations, "
                "news, recipes, guides, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query — be specific for better results",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 5)",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": (
                "Fetch and extract the main text content from a URL. Use this after "
                "web_search to read the full content of a promising result. Returns "
                "the extracted text, not raw HTML."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to fetch content from",
                    },
                },
                "required": ["url"],
            },
        },
    },
]

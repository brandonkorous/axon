"""Media tool schemas — YouTube transcript extraction and summarization."""

from __future__ import annotations

from typing import Any


MEDIA_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "media_youtube_transcript",
            "description": (
                "Extract the transcript (captions) from a YouTube video. Returns the "
                "full text transcript that you can then analyze, summarize, or use for "
                "research. Works with any YouTube URL or video ID."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "YouTube URL or video ID",
                    },
                    "language": {
                        "type": "string",
                        "description": "Preferred language code (default: en)",
                    },
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "media_summarize",
            "description": (
                "Summarize media content (transcript, article, etc.) into a concise "
                "format. Returns a structured summary with key points, topics covered, "
                "and notable quotes or insights."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The content to summarize (transcript, article text, etc.)",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["brief", "detailed", "bullet_points"],
                        "description": "Summary format (default: brief)",
                    },
                    "focus": {
                        "type": "string",
                        "description": "Optional focus area for the summary",
                    },
                },
                "required": ["content"],
            },
        },
    },
]

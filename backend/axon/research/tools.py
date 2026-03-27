"""Research tool schemas — structured research workflow tools."""

from __future__ import annotations

from typing import Any


RESEARCH_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "research_start",
            "description": (
                "Start a structured research task. Defines the scope, depth, and "
                "expected artifact type. Use this to begin a multi-step research "
                "workflow that will produce a polished deliverable in the vault."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Primary research topic or question",
                    },
                    "artifact_type": {
                        "type": "string",
                        "enum": ["report", "analysis", "brief", "comparison"],
                        "description": "Type of deliverable to produce (default: report)",
                    },
                    "depth": {
                        "type": "string",
                        "enum": ["quick", "standard", "deep"],
                        "description": "Research depth — quick (2-3 sources), standard (5-8), deep (10+)",
                    },
                    "focus_areas": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific sub-topics to investigate",
                    },
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "research_add_source",
            "description": (
                "Add a source to the active research task. Sources include web search "
                "results, fetched pages, vault documents, or manually provided data. "
                "Each source is tagged with relevance and reliability."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Source title or label",
                    },
                    "url": {
                        "type": "string",
                        "description": "Source URL (if web-based)",
                    },
                    "content": {
                        "type": "string",
                        "description": "Key content or excerpt from this source",
                    },
                    "relevance": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "How relevant this source is to the research topic",
                    },
                },
                "required": ["title", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "research_synthesize",
            "description": (
                "Synthesize all gathered sources into a coherent analysis. Call this "
                "after adding sources to produce the core content for the artifact. "
                "Returns a structured synthesis with findings, analysis, and conclusions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "synthesis_prompt": {
                        "type": "string",
                        "description": "Optional guidance for synthesis focus or structure",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "research_publish",
            "description": (
                "Publish the research as a polished artifact in the vault. Takes the "
                "synthesized content and generates a formatted deliverable using the "
                "appropriate template. The artifact is saved with full source attribution."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title for the published artifact",
                    },
                    "summary": {
                        "type": "string",
                        "description": "Executive summary or overview",
                    },
                    "findings": {
                        "type": "string",
                        "description": "Key findings section content",
                    },
                    "analysis": {
                        "type": "string",
                        "description": "Detailed analysis section content",
                    },
                    "vault_path": {
                        "type": "string",
                        "description": "Optional vault path override (default: research/{slug})",
                    },
                },
                "required": ["title", "summary", "findings"],
            },
        },
    },
]

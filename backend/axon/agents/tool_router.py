"""Tool router — navigator model pre-selects tools and generates instructions.

The navigator (e.g. Qwen 2.5) picks the right tools so the reasoning
model doesn't have to choose from a huge list.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

MAX_ROUTED_TOOLS = 8  # Skip routing below this threshold

TOOL_SELECTION_PROMPT = """You are a tool router. Given a user message and available tools, select the most relevant and provide a brief instruction.

## User Message
{message}

## Available Tools
{tool_list}

## Instructions
Select 1-5 most relevant tools. Write a 1-2 sentence instruction for the agent.

Respond with JSON only:
```json
{{
  "selected_tools": ["tool_name_1", "tool_name_2"],
  "instruction": "Use tool_name_1 with parameter X to accomplish Y."
}}
```

If no tools are needed, respond: `{{"selected_tools": [], "instruction": ""}}`"""


def _format_tool_list(tools: list[dict[str, Any]]) -> str:
    """Format tool schemas into a concise list for the navigator."""
    lines = []
    for tool in tools:
        func = tool.get("function", {})
        name = func.get("name", "unknown")
        desc = func.get("description", "")
        if len(desc) > 120:
            desc = desc[:117] + "..."
        lines.append(f"- {name}: {desc}")
    return "\n".join(lines)


def _parse_router_response(response: str) -> tuple[list[str], str]:
    """Parse the navigator's JSON response, handling common formatting issues."""
    text = response.strip()

    # Handle markdown code blocks
    if "```json" in text:
        start = text.index("```json") + 7
        end = text.index("```", start)
        text = text[start:end].strip()
    elif "```" in text:
        start = text.index("```") + 3
        end = text.index("```", start)
        text = text[start:end].strip()

    try:
        data = json.loads(text)
        selected = data.get("selected_tools", [])
        instruction = data.get("instruction", "")
        return selected, instruction
    except json.JSONDecodeError:
        logger.warning("[TOOL_ROUTER] Failed to parse navigator response: %s", text[:200])
        return [], ""


async def route_tools(
    navigator_model: str,
    user_message: str,
    available_tools: list[dict[str, Any]],
    *,
    timeout: float = 10.0,
) -> tuple[list[dict[str, Any]], str]:
    """Select relevant tools via navigator. Falls back to full set on failure."""
    import asyncio
    from axon.agents.provider import complete

    # Skip routing for small tool lists — not worth the overhead
    if len(available_tools) <= MAX_ROUTED_TOOLS:
        logger.debug("[TOOL_ROUTER] Skipping — only %d tools", len(available_tools))
        return available_tools, ""

    if not user_message.strip():
        return available_tools, ""

    tool_list_str = _format_tool_list(available_tools)
    prompt = TOOL_SELECTION_PROMPT.format(
        message=user_message[:500],
        tool_list=tool_list_str,
    )

    try:
        result = await asyncio.wait_for(
            complete(
                model=navigator_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.1,
            ),
            timeout=timeout,
        )
        response = result.get("content", "")

        selected_names, instruction = _parse_router_response(response)

        if not selected_names:
            logger.debug("[TOOL_ROUTER] Navigator selected no tools — using full set")
            return available_tools, ""

        # Filter tools to only selected ones, preserving full schemas
        # Always keep vault tools as baseline
        selected_set = set(selected_names)
        filtered = []
        for tool in available_tools:
            name = tool.get("function", {}).get("name", "")
            if name in selected_set or name.startswith("memory_"):
                filtered.append(tool)

        # Safety: if filtering removed too much, fall back to full set
        if len(filtered) < 2:
            logger.debug("[TOOL_ROUTER] Too few tools after filtering — using full set")
            return available_tools, instruction

        logger.info(
            "[TOOL_ROUTER] Routed %d → %d tools. Selected: %s",
            len(available_tools), len(filtered), selected_names,
        )

        return filtered, instruction

    except asyncio.TimeoutError:
        logger.warning("[TOOL_ROUTER] Navigator timed out after %.1fs — using full set", timeout)
        return available_tools, ""
    except Exception as e:
        logger.warning("[TOOL_ROUTER] Navigator failed: %s — using full set", e)
        return available_tools, ""

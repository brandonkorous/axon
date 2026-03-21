"""LLM provider abstraction — wraps LiteLLM for per-agent model configuration."""

from __future__ import annotations

import json
from typing import Any, AsyncIterator

import litellm
from litellm import acompletion

# Suppress LiteLLM's verbose logging
litellm.suppress_debug_info = True


async def stream_completion(
    model: str,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> AsyncIterator[dict[str, Any]]:
    """Stream a completion from any LLM provider via LiteLLM.

    Yields chunks with either text content or tool calls.
    """
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": True,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    response = await acompletion(**kwargs)

    async for chunk in response:
        delta = chunk.choices[0].delta if chunk.choices else None
        if delta is None:
            continue

        # Text content
        if delta.content:
            yield {"type": "text", "content": delta.content}

        # Tool calls
        if delta.tool_calls:
            for tc in delta.tool_calls:
                yield {
                    "type": "tool_call",
                    "id": tc.id,
                    "function": tc.function.name if tc.function else None,
                    "arguments": tc.function.arguments if tc.function else None,
                }

        # Finish reason
        finish = chunk.choices[0].finish_reason if chunk.choices else None
        if finish:
            yield {"type": "finish", "reason": finish}


async def complete(
    model: str,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> dict[str, Any]:
    """Non-streaming completion. Returns the full response."""
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    response = await acompletion(**kwargs)
    message = response.choices[0].message

    result: dict[str, Any] = {"content": message.content or ""}
    if message.tool_calls:
        result["tool_calls"] = [
            {
                "id": tc.id,
                "function": tc.function.name,
                "arguments": tc.function.arguments,
            }
            for tc in message.tool_calls
        ]
    return result

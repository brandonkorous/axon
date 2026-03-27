"""LLM provider abstraction — wraps LiteLLM for per-agent model configuration."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncIterator

import litellm
from litellm import acompletion

logger = logging.getLogger(__name__)

# Suppress LiteLLM's verbose logging
litellm.suppress_debug_info = True

# Timeout for local model calls (seconds) — prevents Ollama queue hangs
LOCAL_MODEL_TIMEOUT = 30


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
        "stream_options": {"include_usage": True},
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    response = await acompletion(**kwargs)

    async for chunk in response:
        delta = chunk.choices[0].delta if chunk.choices else None
        if delta is None:
            # Final chunk may carry usage with no choices
            if hasattr(chunk, "usage") and chunk.usage:
                usage = _extract_stream_usage(model, chunk.usage)
                if usage:
                    yield {"type": "usage", **usage}
            continue

        # Text content
        if delta.content:
            yield {"type": "text", "content": delta.content}

        # Tool calls
        if delta.tool_calls:
            for tc in delta.tool_calls:
                yield {
                    "type": "tool_call",
                    "index": tc.index,
                    "id": tc.id,
                    "function": tc.function.name if tc.function else None,
                    "arguments": tc.function.arguments if tc.function else None,
                }

        # Finish reason
        finish = chunk.choices[0].finish_reason if chunk.choices else None
        if finish:
            yield {"type": "finish", "reason": finish}

        # Usage attached to a chunk with choices
        if hasattr(chunk, "usage") and chunk.usage:
            usage = _extract_stream_usage(model, chunk.usage)
            if usage:
                yield {"type": "usage", **usage}


async def complete(
    model: str,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.7,
    timeout: int | None = None,
) -> dict[str, Any]:
    """Non-streaming completion. Returns the full response."""
    # Apply timeout for local models to prevent Ollama queue hangs
    effective_timeout = timeout
    if effective_timeout is None and model.startswith("ollama/"):
        effective_timeout = LOCAL_MODEL_TIMEOUT

    logger.debug("complete() → model=%s, timeout=%s", model, effective_timeout)

    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    if effective_timeout:
        response = await asyncio.wait_for(
            acompletion(**kwargs), timeout=effective_timeout,
        )
    else:
        response = await acompletion(**kwargs)

    message = response.choices[0].message
    logger.debug("complete() ← %d chars", len(message.content or ""))

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

    # Capture usage metadata
    if hasattr(response, "usage") and response.usage:
        usage = {
            "prompt_tokens": response.usage.prompt_tokens or 0,
            "completion_tokens": response.usage.completion_tokens or 0,
            "total_tokens": response.usage.total_tokens or 0,
        }
        try:
            usage["cost"] = litellm.completion_cost(completion_response=response)
        except Exception as exc:
            logger.warning("Could not calculate cost for model=%s: %s", response.model, exc)
            usage["cost"] = 0.0
        result["usage"] = usage

    return result


def _extract_stream_usage(model: str, usage: Any) -> dict[str, Any] | None:
    """Extract usage dict from a streaming chunk's usage object."""
    prompt = getattr(usage, "prompt_tokens", 0) or 0
    completion = getattr(usage, "completion_tokens", 0) or 0
    total = getattr(usage, "total_tokens", 0) or 0
    if total == 0 and prompt == 0 and completion == 0:
        return None
    cost = 0.0
    try:
        cost = litellm.completion_cost(
            model=model, prompt_tokens=prompt, completion_tokens=completion,
        )
    except Exception as exc:
        logger.warning("Could not calculate cost for model=%s: %s", model, exc)
        cost = 0.0
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": total,
        "cost": cost,
    }

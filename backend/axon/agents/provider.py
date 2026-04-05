"""LLM provider abstraction — wraps LiteLLM for per-agent model configuration."""

from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator

import litellm
from litellm import acompletion

from axon.logging import get_logger

logger = get_logger(__name__)

# Suppress LiteLLM's verbose logging
litellm.suppress_debug_info = True
# Drop params unsupported by specific models (e.g. temperature for GPT-5)
litellm.drop_params = True

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
        "temperature": temperature,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    # gpt-5 models break when max_tokens is set during streaming —
    # the API returns empty content with finish_reason=length.
    # Omit the limit and let the model use its default output cap.
    if not model.startswith("openai/gpt-5"):
        kwargs["max_tokens"] = max_tokens
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    response = await acompletion(**kwargs)

    async for chunk in response:
        delta = chunk.choices[0].delta if chunk.choices else None
        if delta is None:
            # Final chunk may carry usage with no choices
            if hasattr(chunk, "usage") and chunk.usage:
                usage = _extract_stream_usage(model, chunk)
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
            usage = _extract_stream_usage(model, chunk)
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
        usage["cost"] = _extract_cost(response, model, usage["prompt_tokens"], usage["completion_tokens"])
        result["usage"] = usage

    return result


def _extract_cost(response: Any, model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Extract cost from a LiteLLM response, trying multiple sources.

    Priority:
    1. response._hidden_params["response_cost"] — litellm's own calculation
    2. litellm.completion_cost(completion_response=response) — full response object
    3. litellm.completion_cost(model, prompt_tokens, completion_tokens) — manual calc
    """
    # 1. Hidden params (most reliable — litellm computes this internally)
    hidden = getattr(response, "_hidden_params", None)
    if hidden and isinstance(hidden, dict):
        rc = hidden.get("response_cost")
        if rc is not None and rc > 0:
            return float(rc)

    # 2. Full response cost calculation
    try:
        cost = litellm.completion_cost(completion_response=response)
        if cost and cost > 0:
            return float(cost)
    except Exception:
        pass

    # 3. Token-based calculation
    try:
        cost = litellm.completion_cost(
            model=model, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
        )
        if cost and cost > 0:
            return float(cost)
    except Exception as exc:
        logger.warning("Could not calculate cost for model=%s: %s", model, exc)

    return 0.0


def _extract_stream_usage(model: str, chunk: Any) -> dict[str, Any] | None:
    """Extract usage dict from a streaming chunk."""
    usage = chunk.usage
    prompt = getattr(usage, "prompt_tokens", 0) or 0
    completion = getattr(usage, "completion_tokens", 0) or 0
    total = getattr(usage, "total_tokens", 0) or 0
    if total == 0 and prompt == 0 and completion == 0:
        return None

    cost = _extract_cost(chunk, model, prompt, completion)

    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": total,
        "cost": cost,
    }

"""Core Agent class — the conversation loop that drives every persona."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, AsyncIterator

from axon.agents.conversation import Conversation
from axon.agents.provider import stream_completion
from axon.agents.tools import (
    DELEGATION_TOOLS,
    RECRUITMENT_TOOLS,
    VAULT_TOOLS,
    ToolExecutor,
)
from axon.config import PersonaConfig
from axon.vault.navigator import MemoryNavigator
from axon.vault.vault import VaultManager


@dataclass
class StreamChunk:
    """A chunk of streaming output from an agent."""

    agent_id: str
    type: str  # "text", "tool_use", "tool_result", "thinking", "done"
    content: str = ""
    metadata: dict[str, Any] | None = None


class Agent:
    """A single AI agent with a persona, vault, and conversation history.

    The core loop:
    1. Retrieve relevant vault context (deterministic search)
    2. Build messages: system prompt + vault context + history + user message
    3. Stream LLM response
    4. Handle tool calls (vault read/write, delegation, recruitment)
    5. Auto-save check
    """

    def __init__(self, config: PersonaConfig, data_dir: str = "/data"):
        self.config = config
        self.id = config.id
        self.name = config.name

        # Vault and memory
        self.vault = VaultManager(config.vault.path, config.vault.root_file)
        self.navigator = MemoryNavigator(config.vault.path, config.vault.root_file)

        # Tools
        self.tool_executor = ToolExecutor(self.vault, self.id)
        self.tools = self._build_tool_list()

        # Conversation
        self.conversation = Conversation(agent_id=self.id, data_dir=data_dir)

        # System prompt (loaded from file or inline)
        self._system_prompt: str | None = None

    @property
    def system_prompt(self) -> str:
        if self._system_prompt is None:
            self._system_prompt = self.config.load_system_prompt(
                self.config.system_prompt_file
            )
        return self._system_prompt

    @system_prompt.setter
    def system_prompt(self, value: str) -> None:
        self._system_prompt = value

    async def process(self, user_message: str) -> AsyncIterator[StreamChunk]:
        """Process a user message and stream the response."""
        # Signal thinking
        yield StreamChunk(agent_id=self.id, type="thinking")

        # 1. Retrieve vault context
        vault_context = await self.navigator.retrieve(
            query=user_message,
            token_budget=self.config.memory.max_context_tokens,
        )

        # 2. Build messages
        messages = self._build_messages(user_message, vault_context)

        # 3. Add user message to history
        self.conversation.add_user_message(user_message)

        # 4. Stream LLM response with tool handling
        full_response = ""
        tool_calls_buffer: dict[str, dict] = {}  # id -> {function, arguments}

        async for chunk in stream_completion(
            model=self.config.model.reasoning,
            messages=messages,
            tools=self.tools if self.tools else None,
            max_tokens=self.config.model.max_tokens,
            temperature=self.config.model.temperature,
        ):
            if chunk["type"] == "text":
                full_response += chunk["content"]
                yield StreamChunk(
                    agent_id=self.id,
                    type="text",
                    content=chunk["content"],
                )

            elif chunk["type"] == "tool_call":
                tc_id = chunk.get("id")
                if tc_id:
                    if tc_id not in tool_calls_buffer:
                        tool_calls_buffer[tc_id] = {
                            "function": chunk.get("function", ""),
                            "arguments": "",
                        }
                    if chunk.get("function"):
                        tool_calls_buffer[tc_id]["function"] = chunk["function"]
                    if chunk.get("arguments"):
                        tool_calls_buffer[tc_id]["arguments"] += chunk["arguments"]

            elif chunk["type"] == "finish":
                if chunk["reason"] == "tool_calls" and tool_calls_buffer:
                    # Execute tool calls and continue conversation
                    async for sub_chunk in self._handle_tool_calls(
                        messages, tool_calls_buffer, full_response
                    ):
                        if sub_chunk.type == "text":
                            full_response += sub_chunk.content
                        yield sub_chunk
                    tool_calls_buffer = {}

        # 5. Save assistant response to history
        if full_response:
            self.conversation.add_assistant_message(full_response, agent_id=self.id)

        yield StreamChunk(agent_id=self.id, type="done")

    async def generate_greeting(self) -> AsyncIterator[StreamChunk]:
        """Generate the first-message greeting (reads vault, greets in character)."""
        vault_root = self.vault.read_root()
        greeting_prompt = (
            "This is the start of a new conversation. Read the vault context below "
            "for orientation, then greet the user in character. Reference something "
            "from the vault if relevant. Keep it casual and brief.\n\n"
            f"## Vault Root\n{vault_root}"
        )
        async for chunk in self.process(greeting_prompt):
            yield chunk

    def _build_messages(
        self, user_message: str, vault_context: str
    ) -> list[dict[str, Any]]:
        """Build the full message array for the LLM."""
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt},
        ]

        if vault_context:
            messages.append({
                "role": "system",
                "content": f"## Memory (from your vault)\n\n{vault_context}",
            })

        # Add conversation history
        messages.extend(self.conversation.get_llm_messages())

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        return messages

    def _build_tool_list(self) -> list[dict[str, Any]]:
        """Build the tool list based on agent capabilities."""
        tools = list(VAULT_TOOLS)

        if self.config.delegation.can_delegate_to:
            tools.extend(DELEGATION_TOOLS)

        # All agents can request new agents
        tools.extend(RECRUITMENT_TOOLS)

        return tools

    async def _handle_tool_calls(
        self,
        messages: list[dict[str, Any]],
        tool_calls: dict[str, dict],
        response_so_far: str,
    ) -> AsyncIterator[StreamChunk]:
        """Execute tool calls and continue the conversation with results."""
        # Build the assistant message with tool calls
        tool_call_objects = []
        for tc_id, tc_data in tool_calls.items():
            tool_call_objects.append({
                "id": tc_id,
                "type": "function",
                "function": {
                    "name": tc_data["function"],
                    "arguments": tc_data["arguments"],
                },
            })

        assistant_msg: dict[str, Any] = {
            "role": "assistant",
            "content": response_so_far or None,
            "tool_calls": tool_call_objects,
        }
        messages.append(assistant_msg)

        # Execute each tool call
        for tc_id, tc_data in tool_calls.items():
            yield StreamChunk(
                agent_id=self.id,
                type="tool_use",
                content=f"Using: {tc_data['function']}",
                metadata={"tool": tc_data["function"]},
            )

            result = await self.tool_executor.execute(
                tc_data["function"], tc_data["arguments"]
            )

            yield StreamChunk(
                agent_id=self.id,
                type="tool_result",
                content=result[:200],  # Preview for UI
                metadata={"tool": tc_data["function"]},
            )

            messages.append({
                "role": "tool",
                "tool_call_id": tc_id,
                "content": result,
            })

        # Continue conversation with tool results
        async for chunk in stream_completion(
            model=self.config.model.reasoning,
            messages=messages,
            tools=self.tools,
            max_tokens=self.config.model.max_tokens,
            temperature=self.config.model.temperature,
        ):
            if chunk["type"] == "text":
                yield StreamChunk(
                    agent_id=self.id,
                    type="text",
                    content=chunk["content"],
                )

"""Core Agent class — the conversation loop that drives every persona."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, AsyncIterator

from axon.agents.conversation import Conversation, ConversationManager

if TYPE_CHECKING:
    from axon.usage import UsageTracker
from axon.agents.provider import stream_completion
from axon.agents.shared_tools import ACHIEVEMENT_TOOLS, ISSUE_TOOLS, KNOWLEDGE_TOOLS, TASK_TOOLS, SharedVaultToolExecutor
from axon.agents.tools import (
    DELEGATION_TOOLS,
    LEARNING_TOOLS,
    RECRUITMENT_TOOLS,
    VAULT_TOOLS,
    ToolExecutor,
)
from axon.config import PersonaConfig
from axon.lifecycle import AgentLifecycle
from axon.vault.navigator import MemoryNavigator
from axon.vault.vault import VaultManager

logger = logging.getLogger(__name__)


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

    def __init__(
        self,
        config: PersonaConfig,
        data_dir: str = "/data",
        shared_vault: VaultManager | None = None,
        audit_logger: "AuditLogger | None" = None,
        usage_tracker: "UsageTracker | None" = None,
        org_id: str = "",
    ):
        self.config = config
        self.id = config.id
        self._usage_tracker = usage_tracker
        self._org_id = org_id
        self.name = config.name

        # Vault and memory
        self.vault = VaultManager(config.vault.path, config.vault.root_file)
        self.navigator = MemoryNavigator(config.vault.path, config.vault.root_file, cache=self.vault.cache)

        # Memory manager (local LLM for recall + learning)
        self.memory_manager = None
        if config.learning.enabled:
            from axon.vault.memory_manager import MemoryManager

            memory_model = config.learning.memory_model or config.model.navigator
            self.memory_manager = MemoryManager(
                vault=self.vault,
                config=config.learning,
                model=memory_model,
                agent_id=config.id,
                usage_tracker=usage_tracker,
                org_id=org_id,
            )
            logger.debug(
                "[%s] MemoryManager initialized (model=%s, consolidation_interval=%d)",
                config.id, memory_model, config.learning.consolidation_interval,
            )
        else:
            logger.debug("[%s] Learning disabled — using deterministic navigator", config.id)

        # Shared vault (org-level tasks/issues)
        self.shared_vault = shared_vault

        # Conversations (multi-session) — initialized before tools so
        # the tool executor can auto-inject conversation_id into tasks.
        self.conversation_manager = ConversationManager(agent_id=self.id, data_dir=data_dir)

        # Tools
        self.tool_executor = ToolExecutor(
            self.vault, self.id,
            shared_vault=shared_vault,
            audit_logger=audit_logger,
            org_id=org_id,
            memory_manager=self.memory_manager,
            conversation_manager=self.conversation_manager,
        )
        self.tools = self._build_tool_list()

        # Lifecycle (persisted to data/agent-state/)
        state_dir = str(Path(data_dir) / "agent-state")
        self.lifecycle = AgentLifecycle.load(self.id, state_dir)

        # System prompt (loaded from file or inline)
        self._system_prompt: str | None = None

        # Concurrency guard — only one process() at a time per agent
        self._processing_lock = asyncio.Lock()

    @property
    def conversation(self) -> Conversation:
        """Active conversation (backward-compat with single-conversation code)."""
        return self.conversation_manager.active

    @property
    def system_prompt(self) -> str:
        if self._system_prompt is None:
            self._system_prompt = self.config.load_system_prompt(
                self.config.vault.path
            )
        return self._system_prompt

    @system_prompt.setter
    def system_prompt(self, value: str) -> None:
        self._system_prompt = value

    async def process(
        self, user_message: str, *, save_history: bool = True,
    ) -> AsyncIterator[StreamChunk]:
        """Process a user message and stream the response.

        Args:
            save_history: If False, don't add this exchange to conversation
                history (used by scheduler for background tasks).
        """
        # Concurrency guard — skip if agent is already processing
        if self._processing_lock.locked():
            logger.warning("[%s] Already processing — skipping concurrent request", self.id)
            yield StreamChunk(
                agent_id=self.id,
                type="text",
                content="*[I'm currently working on something — please try again in a moment.]*",
            )
            yield StreamChunk(agent_id=self.id, type="done")
            return

        async with self._processing_lock:
            async for chunk in self._process_inner(user_message, save_history=save_history):
                yield chunk

    async def _process_inner(
        self, user_message: str, *, save_history: bool = True,
    ) -> AsyncIterator[StreamChunk]:
        """Internal process — runs under the processing lock."""
        # Check lifecycle state
        status_msg, can_process = self.lifecycle.check_message(user_message)
        if not can_process:
            yield StreamChunk(
                agent_id=self.id,
                type="text",
                content=f"*[{status_msg}]*",
            )
            yield StreamChunk(agent_id=self.id, type="done")
            return

        # Signal thinking
        yield StreamChunk(agent_id=self.id, type="thinking")

        # 1. Retrieve vault context (memory manager or deterministic fallback)
        if self.memory_manager:
            logger.debug("[%s] Using MemoryManager for recall", self.id)
            vault_context = await self.memory_manager.recall(user_message)
        else:
            logger.debug("[%s] Using deterministic navigator for recall", self.id)
            vault_context = await self.navigator.retrieve(
                query=user_message,
                token_budget=self.config.memory.max_context_tokens,
            )
        logger.debug("[%s] Vault context: %d chars", self.id, len(vault_context) if vault_context else 0)

        # 2. Build messages
        messages = self._build_messages(user_message, vault_context)

        # 3. Add user message to history (skip for scheduler-triggered tasks)
        if save_history:
            self.conversation.add_user_message(user_message)

        # 4. Stream LLM response with tool handling
        full_response = ""
        tool_calls_buffer: dict[str, dict] = {}  # id -> {function, arguments}

        try:
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
                    idx = chunk.get("index", 0)
                    if idx not in tool_calls_buffer:
                        tool_calls_buffer[idx] = {
                            "id": chunk.get("id", ""),
                            "function": chunk.get("function", ""),
                            "arguments": "",
                        }
                    if chunk.get("id"):
                        tool_calls_buffer[idx]["id"] = chunk["id"]
                    if chunk.get("function"):
                        tool_calls_buffer[idx]["function"] = chunk["function"]
                    if chunk.get("arguments"):
                        tool_calls_buffer[idx]["arguments"] += chunk["arguments"]

                elif chunk["type"] == "usage":
                    self._record_usage(chunk, "stream", "agent")

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
        except Exception as e:
            yield StreamChunk(
                agent_id=self.id,
                type="text",
                content=f"\n\n*[Error from LLM provider: {e}]*",
            )

        # 5. Save assistant response to history (skip for scheduler-triggered tasks)
        if save_history and full_response:
            self.conversation.add_assistant_message(full_response, agent_id=self.id)

        # 6. Fire async learning (local model extracts insights from this turn)
        if self.memory_manager and full_response:
            logger.debug("[%s] Firing async learning task", self.id)
            asyncio.create_task(self._process_turn_for_learning(
                user_message, full_response, vault_context,
            ))
        elif not self.memory_manager:
            logger.debug("[%s] No memory manager — skipping learning", self.id)

        yield StreamChunk(agent_id=self.id, type="done")

    def _record_usage(
        self, chunk: dict[str, Any], call_type: str, caller: str,
    ) -> None:
        """Record a usage chunk to the usage tracker."""
        if not self._usage_tracker:
            return
        try:
            self._usage_tracker.record(
                model=self.config.model.reasoning,
                prompt_tokens=chunk.get("prompt_tokens", 0),
                completion_tokens=chunk.get("completion_tokens", 0),
                total_tokens=chunk.get("total_tokens", 0),
                cost=chunk.get("cost", 0.0),
                agent_id=self.id,
                org_id=self._org_id,
                call_type=call_type,
                caller=caller,
            )
        except Exception as e:
            logger.debug("Usage recording failed (non-critical): %s", e)

    async def _process_turn_for_learning(
        self, user_message: str, response: str, vault_context: str,
    ) -> None:
        """Fire-and-forget: let the memory manager extract learnings from this turn."""
        try:
            await self.memory_manager.process_turn(user_message, response, vault_context)
        except Exception as e:
            logger.debug("Learning extraction failed (non-critical): %s", e)

    def _get_inbox_summary(self, max_items: int = 5) -> str:
        """Read recent pending inbox items for injection into conversation context."""
        inbox_dir = Path(self.vault.vault_path) / "inbox"
        if not inbox_dir.exists():
            return ""

        items = []
        for md_file in sorted(inbox_dir.glob("*.md"), reverse=True):
            if md_file.name.endswith("-index.md"):
                continue
            if len(items) >= max_items:
                break
            try:
                metadata, body = self.vault.read_file(f"inbox/{md_file.name}")
                if metadata.get("status") != "pending":
                    continue
                item_type = metadata.get("type", "")
                # Only surface actionable notifications (plan results, task completions)
                if item_type not in ("plan_ready", "task_completed", "task_failed"):
                    continue
                from_agent = metadata.get("from", "unknown")
                items.append(f"### From {from_agent} ({item_type})\n{body[:2000]}")
            except Exception:
                continue

        return "\n".join(items)

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
        # Inject agent identity and org context
        identity = (
            f"## Agent Identity\n"
            f"You are **{self.name}** (agent ID: `{self.id}`). "
            f"When you see tasks, inbox items, or references assigned to "
            f"`{self.id}`, those are assigned to **you** — act on them directly.\n\n"
        )

        # Shared org context — tasks, issues, delegation
        org_context = ""
        if self.shared_vault:
            delegates = self.config.delegation.can_delegate_to
            accepts = self.config.delegation.accepts_from
            org_context = (
                "## Organization Tools\n"
                "You have access to a **shared vault** with org-wide tasks and issues.\n\n"
                "### Task workflow\n"
                "1. `task_list` — see all tasks. Filter by `assignee` or `status`.\n"
                "   Output includes the file path like `tasks/2026-03-22-pricing.md`\n"
                "2. `task_update` — update a task. Pass the **exact path** from task_list.\n"
                "   Example: `task_update(path='tasks/2026-03-22-pricing.md', status='in_progress')`\n"
                "3. `task_create` — create new tasks and assign to agents by ID.\n"
                "4. `issue_create` / `issue_list` — for bugs and problems.\n"
                "5. `vault_list('inbox')` — check your inbox for delegated work.\n\n"
                "### Rules\n"
                "- **When asked about your tasks**: call `task_list(assignee='" + self.id + "')` first.\n"
                "- **Tasks assigned to you are YOUR work.** Do the work, don't just report it.\n"
                "  When asked for an update, actually work on the task — research, analyze, "
                "  write findings to your vault, then update the task status.\n"
                "- **Use exact paths** from task_list when calling task_update.\n"
                "- Never refer to yourself in third person. You ARE `" + self.id + "`.\n\n"
            )
            # Async work pattern — tasks with conversation_id get auto-completed
            org_context += (
                "### Async work\n"
                "When a user asks you to do something that requires research, analysis, "
                "writing, or any work beyond what you can answer immediately:\n"
                "1. Create a task with `task_create`, set `assignee` to `" + self.id + "` (yourself)\n"
                "2. Tell the user you're working on it\n"
                "The system will automatically start you on the task and deliver results "
                "back to this conversation. "
                "You do NOT need to call `task_update` — assigning to yourself auto-starts the task.\n\n"
            )

            if delegates:
                names = "any agent" if delegates == ["*"] else ", ".join(delegates)
                org_context += f"You can delegate work to: {names}\n"
            if accepts:
                org_context += f"You accept delegated work from: {', '.join(accepts)}\n"
            org_context += "\n"

        prompt = identity + org_context + self.system_prompt
        if self.lifecycle.strategy_override:
            prompt += f"\n\n## Strategy Override (from user)\n{self.lifecycle.strategy_override}"

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": prompt},
        ]

        if vault_context:
            messages.append({
                "role": "system",
                "content": f"## Memory (from your vault)\n\n{vault_context}",
            })

        # Add conversation history
        messages.extend(self.conversation.get_llm_messages())

        # Inject unread inbox notifications AFTER history so they take priority
        # over any stale conversation context about "waiting for updates"
        inbox_summary = self._get_inbox_summary()
        logger.debug("[%s] Inbox summary: %d chars", self.id, len(inbox_summary))
        if inbox_summary:
            messages.append({
                "role": "user",
                "content": (
                    "[SYSTEM: Inbox Notifications — unread updates from other agents]\n\n"
                    + inbox_summary
                    + "\n\n[Reference these updates when responding. They are current and authoritative.]"
                ),
            })
            messages.append({
                "role": "assistant",
                "content": "Noted — I see the inbox updates and will factor them into my response.",
            })

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        return messages

    def _build_tool_list(self) -> list[dict[str, Any]]:
        """Build the tool list based on agent capabilities."""
        tools = list(VAULT_TOOLS)

        if self.config.delegation.can_delegate_to:
            tools.extend(DELEGATION_TOOLS)

        # Learning tools (outcome linking) when memory manager is active
        if self.memory_manager:
            tools.extend(LEARNING_TOOLS)

        # All agents can request new agents
        tools.extend(RECRUITMENT_TOOLS)

        # Shared vault tools (tasks + issues + achievements + knowledge) when org has a shared vault
        if self.shared_vault:
            tools.extend(TASK_TOOLS)
            tools.extend(ISSUE_TOOLS)
            tools.extend(ACHIEVEMENT_TOOLS)
            tools.extend(KNOWLEDGE_TOOLS)

        return tools

    async def _handle_tool_calls(
        self,
        messages: list[dict[str, Any]],
        tool_calls: dict[int, dict],
        response_so_far: str,
        *,
        depth: int = 0,
    ) -> AsyncIterator[StreamChunk]:
        """Execute tool calls and continue the conversation with results.

        Supports chained tool calls — if the LLM responds with more tool calls
        after seeing results, we recurse (up to MAX_TOOL_CHAIN_DEPTH).
        """
        MAX_TOOL_CHAIN_DEPTH = 10

        if depth >= MAX_TOOL_CHAIN_DEPTH:
            logger.warning("[%s] Hit max tool chain depth (%d) — stopping", self.id, MAX_TOOL_CHAIN_DEPTH)
            yield StreamChunk(
                agent_id=self.id,
                type="text",
                content="\n\n*[Reached maximum tool chain depth — stopping here.]*",
            )
            return

        # Build the assistant message with tool calls
        tool_call_objects = []
        for tc_data in tool_calls.values():
            tool_call_objects.append({
                "id": tc_data["id"],
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
        for tc_data in tool_calls.values():
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
                "tool_call_id": tc_data["id"],
                "content": result,
            })

        # Continue conversation with tool results — handle chained tool calls
        continuation_text = ""
        next_tool_calls: dict[int, dict] = {}

        async for chunk in stream_completion(
            model=self.config.model.reasoning,
            messages=messages,
            tools=self.tools,
            max_tokens=self.config.model.max_tokens,
            temperature=self.config.model.temperature,
        ):
            if chunk["type"] == "text":
                continuation_text += chunk["content"]
                yield StreamChunk(
                    agent_id=self.id,
                    type="text",
                    content=chunk["content"],
                )

            elif chunk["type"] == "tool_call":
                idx = chunk.get("index", 0)
                if idx not in next_tool_calls:
                    next_tool_calls[idx] = {
                        "id": chunk.get("id", ""),
                        "function": chunk.get("function", ""),
                        "arguments": "",
                    }
                if chunk.get("id"):
                    next_tool_calls[idx]["id"] = chunk["id"]
                if chunk.get("function"):
                    next_tool_calls[idx]["function"] = chunk["function"]
                if chunk.get("arguments"):
                    next_tool_calls[idx]["arguments"] += chunk["arguments"]

            elif chunk["type"] == "usage":
                self._record_usage(chunk, "stream", "agent_tool_continuation")

            elif chunk["type"] == "finish":
                if chunk["reason"] == "tool_calls" and next_tool_calls:
                    async for sub_chunk in self._handle_tool_calls(
                        messages, next_tool_calls, continuation_text,
                        depth=depth + 1,
                    ):
                        if sub_chunk.type == "text":
                            continuation_text += sub_chunk.content
                        yield sub_chunk
                    next_tool_calls = {}

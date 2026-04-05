"""Core Agent class — the conversation loop that drives every persona."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, AsyncIterator

from axon.agents.conversation import Conversation, ConversationManager

if TYPE_CHECKING:
    from axon.org import OrgCommsConfig, OrgModelConfig
    from axon.usage import UsageTracker
from axon.agents.provider import complete, stream_completion
from axon.agents.shared_tools import ISSUE_TOOLS, KNOWLEDGE_TOOLS, ORG_SEARCH_TOOLS, SharedVaultToolExecutor
from axon.agents.tools import (
    DELEGATION_TOOLS,
    DISCOVERY_TOOLS,
    PERFORMANCE_TOOLS,
    RECRUITMENT_TOOLS,
    ToolExecutor,
)
from axon.discovery.executor import DiscoveryToolExecutor
from axon.discovery.tools import CAPABILITY_TOOLS
from axon.config import ActionBias, PersonaConfig
from axon.lifecycle import AgentLifecycle
from axon.logging import get_logger
from axon.vault.navigator import MemoryNavigator
from axon.vault.vault import VaultManager

logger = get_logger(__name__)


@dataclass
class StreamChunk:
    """A chunk of streaming output from an agent.

    Types:
    - "text"             — streamed text content
    - "tool_use"         — agent is calling a tool
    - "tool_result"      — tool execution result
    - "thinking"         — agent thinking indicator
    - "done"             — processing complete
    - "route"            — orchestrator routing to another agent
    - "huddle"           — orchestrator opening a huddle
    - "agent_activated"  — a sub-agent has been spawned/delegated to
    - "agent_result"     — a sub-agent has completed its work
    - "ack"              — quick acknowledgment while agent loads context
    """

    agent_id: str
    type: str
    content: str = ""
    metadata: dict[str, Any] | None = None


# Prompt for the local model to generate a brief acknowledgment
ACK_SYSTEM_PROMPT = (
    "You are a brief, warm AI assistant. Given the user's message, respond with "
    "a single short sentence (under 15 words) acknowledging what they asked and "
    "indicating you're looking into it. Be natural, not robotic. "
    "Do NOT answer the question — just acknowledge it. "
    "Do NOT use filler like 'Sure!' or 'Of course!' every time — vary your tone. "
    "Match the energy: casual question gets casual ack, serious question gets focused ack."
)
ACK_MAX_TOKENS = 48
ACK_TIMEOUT = 5  # seconds — if local model can't ack in 5s, skip it


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
        org_comms_config: "OrgCommsConfig | None" = None,
        org_model_config: "OrgModelConfig | None" = None,
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
        self._vector_store = None
        if config.learning.enabled:
            from axon.vault.memory_manager import MemoryManager

            # Initialize vector store for semantic search
            try:
                from axon.vault.embeddings import EmbeddingClient
                from axon.vault.vector_store import VaultVectorStore

                embedding_client = EmbeddingClient(
                    model_name=config.learning.embedding_model,
                )
                self._vector_store = VaultVectorStore(
                    vault_path=config.vault.path,
                    embedding_client=embedding_client,
                    dimensions=config.learning.embedding_dimensions,
                )
            except Exception as e:
                logger.warning(
                    "vector_store_init_failed",
                    agent_id=config.id, error=str(e),
                )

            # Resolve memory model: agent config → org memory role → navigator
            memory_model = config.learning.memory_model
            if not memory_model and org_model_config and org_model_config.roles.memory:
                memory_model = org_model_config.roles.memory
            if not memory_model:
                memory_model = config.model.navigator
            self.memory_manager = MemoryManager(
                vault=self.vault,
                config=config.learning,
                model=memory_model,
                agent_id=config.id,
                usage_tracker=usage_tracker,
                org_id=org_id,
                vector_store=self._vector_store,
            )
            logger.debug(
                "memory_manager_initialized",
                agent_id=config.id, model=memory_model,
                consolidation_interval=config.learning.consolidation_interval,
                vector_store=self._vector_store is not None,
            )
        else:
            logger.debug("learning_disabled", agent_id=config.id)

        # Reasoning engine (structured decision making)
        self.reasoning_engine = None
        if config.reasoning and config.reasoning.enabled:
            from axon.reasoning.engine import ReasoningEngine

            reasoning_model = config.reasoning.model or config.model.reasoning
            bg_model = config.reasoning.background_model or (
                config.learning.memory_model if config.learning.enabled else ""
            )
            self.reasoning_engine = ReasoningEngine(
                vault=self.vault,
                config=config.reasoning,
                model=reasoning_model,
                background_model=bg_model or reasoning_model,
                agent_id=config.id,
                usage_tracker=usage_tracker,
                org_id=org_id,
            )
            logger.debug(
                "[%s] ReasoningEngine initialized (model=%s, bg=%s)",
                config.id, reasoning_model, bg_model or reasoning_model,
            )

        # Shared vault (org-level tasks/issues)
        self.shared_vault = shared_vault

        # Conversations (multi-session) — initialized before tools so
        # the tool executor can auto-inject conversation_id into tasks.
        self.conversation_manager = ConversationManager(agent_id=self.id, data_dir=data_dir)

        # Comms executor (email, Discord, contacts)
        self._comms_executor = None
        if config.comms.enabled and shared_vault and org_comms_config:
            from axon.comms.executor import CommsToolExecutor
            self._comms_executor = CommsToolExecutor(
                shared_vault=shared_vault,
                agent_id=self.id,
                org_id=org_id,
                org_comms_config=org_comms_config,
                email_alias=config.comms.email_alias,
                agent_display_name=self.name,
            )

        # Web executor (search, fetch, synthesis)
        self._web_executor = None
        if config.web.enabled:
            from axon.web.executor import WebToolExecutor
            self._web_executor = WebToolExecutor(config=config.web)

        # Media executor (YouTube transcripts, summarization)
        self._media_executor = None
        if config.media.enabled:
            from axon.media.executor import MediaToolExecutor
            self._media_executor = MediaToolExecutor(config=config.media)

        # Browser executor (Playwright-based web automation)
        self._browser_executor = None
        if config.browser.enabled:
            from axon.browser.executor import BrowserToolExecutor
            self._browser_executor = BrowserToolExecutor(config=config.browser)

        # Integration executor (external service plugins)
        self._integration_executor = None
        if config.integrations.enabled:
            from axon.integrations.registry import create_integration_executor
            self._integration_executor = create_integration_executor(
                config.integrations.enabled,
            )

        # Discovery executor (capability introspection and self-provisioning)
        self._discovery_executor = DiscoveryToolExecutor(
            agent_id=self.id,
            org_id=org_id,
            get_config=lambda: self.config,
            get_shared_vault=lambda: self.shared_vault,
            on_capability_enabled=self._on_capability_enabled,
        )

        # Tools
        self.tool_executor = ToolExecutor(
            self.vault, self.id,
            shared_vault=shared_vault,
            audit_logger=audit_logger,
            org_id=org_id,
            memory_manager=self.memory_manager,
            reasoning_engine=self.reasoning_engine,
            conversation_manager=self.conversation_manager,
            comms_executor=self._comms_executor,
            web_executor=self._web_executor,
            browser_executor=self._browser_executor,
            media_executor=self._media_executor,
            integration_executor=self._integration_executor,
            discovery_executor=self._discovery_executor,
        )
        self.tool_executor._stream_callback = self._buffer_tool_stream_event
        self._pending_tool_events: list[StreamChunk] = []

        # Plugin executor — routes tool calls to enabled plugins
        self._plugin_executor = self._build_plugin_executor()
        if self._plugin_executor:
            self.tool_executor._plugin_executor = self._plugin_executor

        self.tools = self._build_tool_list()

        # Lifecycle (persisted to data/agent-state/)
        state_dir = str(Path(data_dir) / "agent-state")
        self.lifecycle = AgentLifecycle.load(self.id, state_dir)

        # Peer roster (injected after all agents are initialized)
        self._peer_roster: str = ""

        # Org principles (injected from shared vault principles.md)
        self._org_principles: str = ""

        # Self-regulation tracker (prevents agent spiraling)
        self._regulation_tracker = None
        if config.self_regulation.enabled:
            from axon.self_regulation import SelfRegulationTracker
            self._regulation_tracker = SelfRegulationTracker(config.self_regulation)

        # System prompt (loaded from file or inline)
        self._system_prompt: str | None = None

        # Concurrency guard — only one process() at a time per agent
        self._processing_lock = asyncio.Lock()

    async def setup(self) -> None:
        """Async post-init — initialize agent DB, build index, load credentials."""
        from axon.db.agent_engine import init_agent_db
        from axon.db.crud.vault_index import rebuild_index

        self._agent_db = await init_agent_db(self.config.vault.path)

        # Populate vault index from markdown files
        async with self._agent_db() as session:
            count = await rebuild_index(session, self.config.vault.path)
        logger.debug("[%s] agent.db initialized, %d files indexed", self.id, count)

        # Sync vault file changes to agent.db
        self.vault.on_change(self._on_vault_change)

        if not self._integration_executor:
            return
        from axon.integrations.credentials import load_integration_credentials
        credentials_map = await load_integration_credentials(
            self._org_id, self.config.integrations.enabled,
        )
        if credentials_map:
            from axon.integrations.registry import create_integration_executor
            self._integration_executor = create_integration_executor(
                self.config.integrations.enabled, credentials_map,
            )
            self.tool_executor._integration_executor = self._integration_executor
            self.tools = self._build_tool_list()

    async def _on_capability_enabled(self, cap_type: str, name: str) -> None:
        """Called by DiscoveryToolExecutor after auto-enabling a capability.

        Rebuilds the tool list so the agent can use it immediately.
        """
        logger.info("[%s] Capability auto-enabled: %s '%s' — rebuilding tools", self.id, cap_type, name)
        self.tools = self._build_tool_list()

    def build_roster(self, all_configs: dict[str, "PersonaConfig"]) -> None:
        """Build a peer roster from org agent configs.

        Includes: parent, siblings (same parent_id), and direct children.
        For top-level agents (no parent_id), peers are other top-level agents.
        Each entry includes the agent's domains so peers know who handles what.
        """
        my_parent = self.config.parent_id
        lines: list[str] = []

        for aid, cfg in all_configs.items():
            if aid == self.id:
                continue
            if cfg.type.value in ("orchestrator", "huddle"):
                continue

            is_parent = (aid == my_parent)
            is_sibling = (cfg.parent_id == my_parent) if my_parent else (not cfg.parent_id)
            is_child = (cfg.parent_id == self.id)

            if not (is_parent or is_sibling or is_child):
                continue

            relation = "parent" if is_parent else "report" if is_child else "peer"
            line = f"- **{cfg.name}** (`{aid}`): {cfg.title}"
            if cfg.tagline:
                line += f" — {cfg.tagline}"
            # Include domains so agents know what each peer handles
            domains = cfg.guardrails.domains.allowed_domains if cfg.guardrails.has_domain_boundaries else []
            if domains:
                line += f"  · Domains: {', '.join(domains)}"
            line += f"  [{relation}]"
            lines.append(line)

        self._peer_roster = "\n".join(lines)

    async def _buffer_tool_stream_event(self, chunk: StreamChunk) -> None:
        """Buffer a stream event from tool execution for emission during processing."""
        self._pending_tool_events.append(chunk)

    def _on_vault_change(self, relative_path: str, event: str) -> None:
        """Sync a vault file change to agent.db (called by VaultManager)."""
        import asyncio
        from axon.db.crud.vault_index import upsert_entry, remove_entry
        from axon.vault.frontmatter import parse_frontmatter

        if not hasattr(self, "_agent_db") or self._agent_db is None:
            return

        async def _sync():
            async with self._agent_db() as session:
                if event == "remove":
                    await remove_entry(session, relative_path)
                    return
                # Read file and upsert
                try:
                    cached = self.vault.cache.get(relative_path)
                    if cached:
                        metadata, body = cached.metadata, cached.body
                    else:
                        raw = (self.vault.vault_path / relative_path).read_text(encoding="utf-8")
                        metadata, body = parse_frontmatter(raw)
                    tags = metadata.get("tags", "")
                    if isinstance(tags, list):
                        tags = ", ".join(tags)
                    await upsert_entry(session, {
                        "path": relative_path,
                        "name": str(metadata.get("name", "")),
                        "description": str(metadata.get("description", "")),
                        "type": str(metadata.get("type", "")),
                        "tags": str(tags),
                        "content_preview": body[:500],
                        "confidence": float(metadata.get("confidence", 0.5)),
                        "status": str(metadata.get("status", "active")),
                        "learning_type": str(metadata.get("learning_type", "")),
                        "date": str(metadata.get("date", "")),
                    })
                except Exception:
                    logger.debug("[%s] Failed to sync %s to agent.db", self.id, relative_path)

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_sync())
        except RuntimeError:
            pass  # No event loop — skip sync

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

    async def _retrieve_vault_context(self, user_message: str) -> str:
        """Retrieve vault context via memory manager or deterministic fallback."""
        if self.memory_manager:
            logger.debug("[%s] Using MemoryManager for recall", self.id)
            return await self.memory_manager.recall(user_message)
        logger.debug("[%s] Using deterministic navigator for recall", self.id)
        return await self.navigator.retrieve(
            query=user_message,
            token_budget=self.config.memory.max_context_tokens,
        )

    async def _generate_ack(self, user_message: str) -> str | None:
        """Generate a quick acknowledgment using the local model.

        Returns None if the local model is unavailable or too slow.
        """
        ack_model = (
            self.config.learning.memory_model
            if self.config.learning.enabled
            else self.config.model.navigator
        )
        if not ack_model:
            logger.debug("[%s] Ack skipped — no local model configured", self.id)
            return None

        logger.debug("[%s] Generating ack with model=%s", self.id, ack_model)
        try:
            result = await asyncio.wait_for(
                complete(
                    model=ack_model,
                    messages=[
                        {"role": "system", "content": ACK_SYSTEM_PROMPT},
                        {"role": "user", "content": user_message},
                    ],
                    max_tokens=ACK_MAX_TOKENS,
                    temperature=0.8,
                ),
                timeout=ACK_TIMEOUT,
            )
            ack = (result.get("content") or "").strip()
            if ack:
                logger.debug("[%s] Ack generated: %s", self.id, ack)
            return ack or None
        except TimeoutError:
            logger.warning("[%s] Ack generation timed out (>%ds) — skipping", self.id, ACK_TIMEOUT)
            return None
        except Exception as e:
            logger.warning("[%s] Ack generation failed — skipping: %s", self.id, e)
            return None

    async def process(
        self, user_message: str, *, save_history: bool = True,
        attachments: list[dict] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        """Process a user message and stream the response.

        Args:
            save_history: If False, don't add this exchange to conversation
                history (used by scheduler for background tasks).
            attachments: Optional list of file attachment metadata dicts
                (path, name, type, size) from the upload endpoint.
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
            async for chunk in self._process_inner(
                user_message, save_history=save_history, attachments=attachments,
            ):
                yield chunk

    async def _process_inner(
        self, user_message: str, *, save_history: bool = True,
        attachments: list[dict] | None = None,
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

        # 1. Kick off vault retrieval, task context, and ack generation in parallel
        vault_task = asyncio.create_task(self._retrieve_vault_context(user_message))
        task_ctx_task = asyncio.create_task(self._retrieve_task_context())
        ack_task = asyncio.create_task(self._generate_ack(user_message))

        # Yield ack as soon as it's ready (don't wait for vault/tasks)
        ack_text = await ack_task
        if ack_text:
            yield StreamChunk(agent_id=self.id, type="ack", content=ack_text)

        # Wait for vault and task context to finish
        vault_context = await vault_task
        task_context = await task_ctx_task
        logger.debug("[%s] Vault context: %d chars", self.id, len(vault_context) if vault_context else 0)

        # 2. Classify intent and build targeted tool list + messages
        from axon.agents.intent_router import classify_intent
        routing = classify_intent(user_message)
        logger.debug(
            "[%s] Intent: %s (confidence=%.2f, tools=%s, patterns=%s)",
            self.id, routing.intent, routing.confidence,
            routing.tool_groups, routing.pattern_names,
        )
        routed_tools = self._build_tool_list(routing.tool_groups)

        # 2b. Use navigator model to further filter tools and generate instruction
        tool_instruction = ""
        if self.config.model.navigator and len(routed_tools) > 8:
            from axon.agents.tool_router import route_tools
            routed_tools, tool_instruction = await route_tools(
                navigator_model=self.config.model.navigator,
                user_message=user_message,
                available_tools=routed_tools,
            )
            if tool_instruction:
                logger.debug("[%s] Tool instruction: %s", self.id, tool_instruction[:100])

        messages = self._build_messages(
            user_message, vault_context, routing.pattern_names,
            tool_instruction=tool_instruction, task_context=task_context,
            attachments=attachments,
        )

        # 3. Add user message to history (skip for scheduler-triggered tasks)
        if save_history:
            metadata = {"attachments": attachments} if attachments else None
            self.conversation.add_user_message(user_message, metadata=metadata)

        # 4. Stream LLM response with tool handling
        full_response = ""
        tool_calls_buffer: dict[str, dict] = {}  # id -> {function, arguments}

        try:
            async for chunk in stream_completion(
                model=self.config.model.reasoning,
                messages=messages,
                tools=routed_tools if routed_tools else None,
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

        # 5b. Extract structured output if any active skill defines output fields
        if full_response:
            from axon.structured_output import extract_structured_output, StructuredResult
            output_fields = self._get_active_output_fields(user_message)
            structured_data = extract_structured_output(full_response, output_fields)
            if structured_data:
                result = StructuredResult(
                    schema_name=self.id,
                    data=structured_data,
                    agent_id=self.id,
                    confidence=structured_data.get("confidence", 0.5),
                )
                yield StreamChunk(
                    agent_id=self.id,
                    type="structured_output",
                    content="",
                    metadata=result.model_dump(),
                )

        # 6. Fire async learning (local model extracts insights from this turn)
        if self.memory_manager and full_response:
            logger.debug("[%s] Firing async learning task", self.id)
            asyncio.create_task(self._process_turn_for_learning(
                user_message, full_response, vault_context,
            ))
        elif not self.memory_manager:
            logger.debug("[%s] No memory manager — skipping learning", self.id)

        # 7. Fire async task management (local model creates/updates tasks)
        if self.shared_vault and full_response:
            asyncio.create_task(self._process_turn_for_tasks(
                user_message, full_response, task_context,
            ))

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
        """Fire-and-forget: let the memory manager extract memories from this turn."""
        try:
            conv_id = ""
            if self.conversation_manager:
                conv_id = self.conversation_manager.active_id
            elif self.conversation and self.conversation.conversation_id:
                conv_id = self.conversation.conversation_id
            await self.memory_manager.process_turn(
                user_message, response, vault_context,
                conversation_id=conv_id,
            )
        except Exception as e:
            logger.debug("Learning extraction failed (non-critical): %s", e)

    async def _retrieve_task_context(self) -> str:
        """Pre-processing: load active tasks assigned to this agent."""
        if not self.shared_vault:
            return ""
        try:
            from axon.vault.task_pipeline import recall_tasks
            return await recall_tasks(self.shared_vault, self.id)
        except Exception as e:
            logger.debug("Task context retrieval failed (non-critical): %s", e)
            return ""

    async def _process_turn_for_tasks(
        self, user_message: str, response: str, task_context: str,
    ) -> None:
        """Fire-and-forget: let local LLM manage tasks from this turn."""
        try:
            from axon.vault.task_pipeline import process_turn_for_tasks
            memory_model = ""
            if self.memory_manager:
                memory_model = self.memory_manager.model
            await process_turn_for_tasks(
                user_message, response, self.id, self.shared_vault,
                task_context, memory_model=memory_model, org_id=self._org_id,
            )
        except Exception as e:
            logger.debug("Task pipeline failed (non-critical): %s", e)

    def _get_active_output_fields(self, user_message: str) -> list | None:
        """Get output fields from active skills for this message."""
        if not hasattr(self.config, "skills") or not self.config.skills or not self.config.skills.enabled:
            return None
        from axon.skills.resolver import resolve_skills_for_message, get_active_output_fields
        active = resolve_skills_for_message(user_message, self.config.skills.enabled)
        fields = get_active_output_fields(active)
        return fields if fields else None

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
        self, user_message: str, vault_context: str,
        routed_patterns: list[str] | None = None,
        tool_instruction: str = "",
        task_context: str = "",
        attachments: list[dict] | None = None,
    ) -> list[dict[str, Any]]:
        """Build the full message array for the LLM."""
        # Inject agent identity and org context
        identity = (
            f"## Agent Identity\n"
            f"You are **{self.name}** (agent ID: `{self.id}`). "
            f"When you see tasks or references assigned to "
            f"`{self.id}`, those are assigned to **you** — act on them directly.\n\n"
            f"## Personal Vault\n"
            f"You have a personal knowledge vault. Use it actively:\n"
            f"- **Before responding**, check your vault for relevant context "
            f"(`memory_search`, `memory_list`).\n"
            f"- **After learning something important**, store it "
            f"(`memory_write`) so you can reference it later.\n"
            f"- Your vault is your memory across conversations — "
            f"decisions, research, insights, and working notes belong there.\n\n"
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
                "5. `task_list(assignee='" + self.id + "')` — check for assigned tasks.\n\n"
                "### Rules\n"
                "- **When asked about your tasks**: call `task_list(assignee='" + self.id + "')` first.\n"
                "- **Tasks assigned to you are YOUR responsibility.** "
                + ("Use `delegate_task` to assign implementation work to your delegates, "
                   "then track and relay results. "
                   if delegates else
                   "Do the work, don't just report it. "
                   "When asked for an update, actually work on the task — research, analyze, "
                   "write findings to your vault, then update the task status. ")
                + "\n"
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

        # Capability self-awareness — agents should know they can discover and request tools
        discovery_section = (
            "## Capability Self-Awareness\n"
            "You have access to capability discovery tools. **Use them.**\n\n"
            "### When to discover\n"
            "- When someone asks what tools you have or need — call `plugins_discover` "
            "to see what's **actually available**, not just what you currently have.\n"
            "- When you realize you **can't** do something (browse a site, generate a PDF, "
            "run code, process images) — search for a capability that would let you.\n"
            "- When asked to inspect, audit, or interact with external resources and you "
            "lack the tools — don't just say \"I can't\". Search first.\n\n"
            "### When to request\n"
            "- If `plugins_discover` finds something you need but don't have enabled, "
            "use `plugins_enable` to enable it.\n"
            "- If nothing exists for what you need, use `plugins_request` to flag the gap.\n\n"
            "### Critical rule\n"
            "**Never say \"I have everything I need\" without checking.** If your role "
            "implies you should be able to do something (e.g., a design lead should be able "
            "to inspect the product's website), and you can't — that's a gap. Discover it, "
            "request it, don't ignore it.\n\n"
        )

        # Comms instructions — when agent has comms tools
        comms_section = ""
        if self._comms_executor:
            comms_section = (
                "## Communications\n"
                "You have direct access to communication tools (`comms_send_email`, "
                "`comms_send_discord`, `comms_send_slack`, `comms_send_teams`, "
                "`comms_send_zoom`, `comms_create_zoom_meeting`, "
                "`comms_create_teams_meeting`, `comms_create_discord_event`).\n\n"
                "### Rules\n"
                "- **Always use your comms tools directly.** Never delegate sending messages "
                "or creating meetings to workers or other agents.\n"
                "- **Discord, Slack, Teams, and Zoom channel IDs are numeric.** "
                "Never use channel names — use the numeric ID. If you don't know the ID, "
                "ask the user.\n"
                "- **Use `comms_lookup_contact`** to find email addresses before sending email.\n"
                "- Messages may require user approval before sending (depending on org settings).\n"
            )
            # Inject configured channel mappings so agents know what's available
            config = self._comms_executor.config
            known_channels: list[str] = []
            if config.discord and config.discord.channel_mappings:
                for cid in config.discord.channel_mappings:
                    known_channels.append(f"Discord channel `{cid}`")
            if config.slack and config.slack.channel_mappings:
                for cid in config.slack.channel_mappings:
                    known_channels.append(f"Slack channel `{cid}`")
            if config.teams and config.teams.channel_mappings:
                for cid in config.teams.channel_mappings:
                    known_channels.append(f"Teams channel `{cid}`")
            if config.zoom and config.zoom.channel_mappings:
                for cid in config.zoom.channel_mappings:
                    known_channels.append(f"Zoom channel `{cid}`")
            if known_channels:
                comms_section += "### Known channels\n" + "\n".join(f"- {c}" for c in known_channels) + "\n\n"

        # Peer roster — immediate teammates (parent, siblings, direct reports)
        roster_section = ""
        if self._peer_roster:
            delegates = self.config.delegation.can_delegate_to
            delegate_note = ""
            if delegates:
                names = "any agent" if delegates == ["*"] else ", ".join(f"`{d}`" for d in delegates)
                delegate_note = f"\nYou can delegate work to: {names}. Use `find_agents` to discover others.\n"
            roster_section = (
                "## Your Team\n"
                "These agents are your immediate colleagues:\n\n"
                f"{self._peer_roster}\n"
                f"{delegate_note}\n"
            )

        # Action Priority Protocol — how agents decide to act vs. respond
        action_section = self._build_action_priority_section()

        # Org principles — shared values/culture injected for all agents
        principles_section = ""
        if self._org_principles:
            principles_section = f"## Organization Principles\n{self._org_principles}\n\n"

        # Agent guardrails — domain boundaries injected into prompt
        guardrails_section = self.config.guardrails.build_boundary_prompt()

        # Confidence gates — mode-specific instructions
        confidence_section = self.config.confidence.build_confidence_prompt()

        prompt = (
            identity
            + action_section
            + principles_section
            + org_context
            + discovery_section
            + guardrails_section
            + confidence_section
            + comms_section
            + roster_section
            + self.system_prompt
        )
        if self.lifecycle.strategy_override:
            prompt += f"\n\n## Strategy Override (from user)\n{self.lifecycle.strategy_override}"

        # Inject cognitive skill methodologies if any are active
        if hasattr(self.config, "skills") and self.config.skills and self.config.skills.enabled:
            from axon.skills.resolver import resolve_skills_for_message, build_skill_prompt
            active_skills = resolve_skills_for_message(user_message, self.config.skills.enabled)
            skill_prompt = build_skill_prompt(active_skills)
            if skill_prompt:
                prompt += f"\n\n{skill_prompt}"

        # Inject cognitive patterns — filtered by intent router when available
        from axon.patterns.resolver import resolve_patterns_for_agent, build_pattern_prompt
        if routed_patterns is not None:
            # Intent router selected specific patterns for this message
            explicit = routed_patterns if routed_patterns else None
        else:
            explicit = getattr(self.config, "cognitive_patterns", None) or []
            explicit = explicit or None
        patterns = resolve_patterns_for_agent(self.config.title, explicit)
        pattern_prompt = build_pattern_prompt(patterns)
        if pattern_prompt:
            prompt += f"\n\n{pattern_prompt}"

        if tool_instruction:
            prompt += f"\n\n## Tool Guidance\n{tool_instruction}"

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": prompt},
        ]

        if vault_context:
            messages.append({
                "role": "system",
                "content": f"## Memory (from your vault)\n\n{vault_context}",
            })

        if task_context:
            messages.append({
                "role": "system",
                "content": task_context,
            })

        # NO raw conversation history replay. Context comes from vault memory
        # (short-term + long-term). The memory manager extracts and stores
        # relevant context from each turn, so the agent has continuity
        # without burning tokens on full chat replay.

        # Add current user message — multimodal if attachments include images
        if attachments:
            content_blocks: list[dict[str, Any]] = []
            if user_message:
                content_blocks.append({"type": "text", "text": user_message})
            for att in attachments:
                att_type = att.get("type", "")
                if att_type.startswith("image/"):
                    file_path = Path(self.conversation_manager.data_dir) / att["path"]
                    try:
                        import base64 as _b64
                        b64data = _b64.b64encode(file_path.read_bytes()).decode("ascii")
                        content_blocks.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:{att_type};base64,{b64data}"},
                        })
                    except Exception as exc:
                        logger.warning("Failed to read attachment %s: %s", att["path"], exc)
                        content_blocks.append({
                            "type": "text",
                            "text": f"\n[Attached image could not be loaded: {att['name']}]",
                        })
                else:
                    content_blocks.append({
                        "type": "text",
                        "text": f"\n[Attached file: {att['name']} ({att_type}, {att['size']} bytes)]",
                    })
            messages.append({"role": "user", "content": content_blocks})
        else:
            messages.append({"role": "user", "content": user_message})

        return messages

    def _rebuild_comms(self, org_comms_config) -> None:
        """Hot-reload comms executor and tools after config change."""
        has_channel = bool(
            getattr(org_comms_config, "email_domain", "")
            or getattr(org_comms_config, "discord", None) and org_comms_config.discord.guild_id
            or getattr(org_comms_config, "slack", None) and org_comms_config.slack.channel_mappings
        )
        if self.config.comms.enabled and self.shared_vault and org_comms_config and has_channel:
            from axon.comms.executor import CommsToolExecutor
            self._comms_executor = CommsToolExecutor(
                shared_vault=self.shared_vault,
                agent_id=self.id,
                org_id=self._org_id,
                org_comms_config=org_comms_config,
                email_alias=self.config.comms.email_alias,
                agent_display_name=self.name,
            )
        else:
            self._comms_executor = None
        self.tool_executor._comms_executor = self._comms_executor
        self.tools = self._build_tool_list()

    def _build_action_priority_section(self) -> str:
        """Build the Action Priority Protocol prompt based on action_bias."""
        bias = self.config.behavior.action_bias

        # Core protocol — always included
        protocol = (
            "## Action Priority Protocol\n"
            "You are an agent, not a chatbot. You have tools — use them. "
            "When you can act, act. When you can't, say what you need in order to act.\n\n"
            "On every turn, follow this priority:\n\n"
            "1. **ACT** — If you have a tool that fulfills the request, call it immediately. "
            "Never describe what you would do — just do it. "
            "If asked to submit, send, create, hire, or request something, use the appropriate tool.\n"
            "2. **DELEGATE** — If the request is outside your domain but a teammate handles it, "
            "use `delegate_task` to route it. Check your team roster for who owns what.\n"
            "3. **RECRUIT** — If you need a capability that nobody on the team has, "
            "use `request_agent` to propose a new agent. Don't wait to be told — identify the gap and act.\n"
            "4. **RESPOND** — Only fall back to a text response when you're explicitly asked for "
            "analysis, opinions, or brainstorming, or when no tool exists for the action.\n\n"
        )

        # Recruitment guidance — when and how to hire
        protocol += (
            "### When to Recruit\n"
            "- **Capability gap.** A request needs sustained, specialist effort outside your domain — "
            "don't fake expertise you don't have. A shallow answer is worse than no answer.\n"
            "- **Repeated need.** The same type of request keeps coming up and no one on the team covers it.\n"
            "- **Quality gap.** You or a teammate are producing shallow output on a topic that isn't your specialty.\n\n"
            "Before recruiting, check if an existing teammate covers the need (`find_agents`). "
            "If someone fits, `delegate_task`. If no one fits, use `request_agent`.\n\n"
            "**IMPORTANT: To hire or recruit a new agent, ALWAYS use `request_agent`. "
            "Do NOT use `task_create` for hiring — `task_create` creates a task, not an agent. "
            "Only `request_agent` triggers the recruitment pipeline that actually creates a new team member.** "
            "Provide the role, reason, and a description of what the agent should do. "
            "The system will automatically craft a detailed persona from your brief.\n\n"
        )

        # Anti-patterns — always included
        protocol += (
            "**Never do these:**\n"
            "- Say \"I will prepare...\" or \"Here's what I would submit...\" — call the tool instead.\n"
            "- Output a formatted document as text when a tool call would actually submit it.\n"
            "- Ask for permission to use a tool you already have access to.\n"
            "- Use `task_create` when you mean to hire — use `request_agent` instead.\n"
            "- Narrate actions instead of performing them.\n\n"
        )

        # Bias-specific tuning
        if bias == ActionBias.PROACTIVE:
            protocol += (
                "**Your action bias is `proactive`:** Act first, explain after. "
                "If a tool might apply, use it. Err on the side of doing.\n\n"
            )
        elif bias == ActionBias.DELIBERATIVE:
            protocol += (
                "**Your action bias is `deliberative`:** Think before acting on high-stakes operations "
                "(financial commitments, external communications, irreversible changes). "
                "For these, confirm intent before calling the tool. For everything else, act immediately.\n\n"
            )
        else:  # balanced
            protocol += (
                "**Your action bias is `balanced`:** Act immediately on clear requests. "
                "On ambiguous requests, briefly clarify before acting.\n\n"
            )

        return protocol

    def _build_plugin_executor(self) -> "PluginToolExecutor | None":
        """Create a PluginToolExecutor from org-level plugin instances."""
        from axon.plugins.executor import PluginToolExecutor
        from axon.plugins.registry import PLUGIN_REGISTRY
        import axon.registry as reg

        # Collect instances assigned to this agent from org config
        org = reg.org_registry.get(self._org_id)
        if not org or not org.config.plugin_instances:
            return None

        my_instances = [
            inst for inst in org.config.plugin_instances
            if self.id in inst.agents
        ]
        if not my_instances:
            return None

        # Build instance_map: {plugin_name: [(instance_id, plugin_obj), ...]}
        instance_map: dict[str, list[tuple[str, "BasePlugin"]]] = {}
        for inst in my_instances:
            cls = PLUGIN_REGISTRY.get(inst.plugin)
            if not cls:
                continue
            try:
                plugin_obj = cls(
                    agent_id=self.id,
                    org_id=self._org_id,
                    instance_id=inst.id,
                    **inst.config,
                )
                plugin_obj.on_load()
                instance_map.setdefault(inst.plugin, []).append(
                    (inst.id, plugin_obj),
                )
            except Exception as e:
                logger.warning(
                    "[%s] Failed to load plugin instance '%s': %s",
                    self.id, inst.id, e,
                )

        if not instance_map:
            return None

        return PluginToolExecutor(instance_map)

    def _build_tool_list(self, tool_groups: list[str] | None = None) -> list[dict[str, Any]]:
        """Build the tool list based on agent capabilities and intent routing.

        When tool_groups is provided (from intent router), only include tools
        for the specified groups. Otherwise includes all available tools.
        """
        from axon.agents.intent_router import (
            TOOL_GROUP_BROWSER, TOOL_GROUP_COMMS,
            TOOL_GROUP_DELEGATION, TOOL_GROUP_DISCOVERY, TOOL_GROUP_ISSUES,
            TOOL_GROUP_KNOWLEDGE, TOOL_GROUP_MEDIA, TOOL_GROUP_ORG_SEARCH,
            TOOL_GROUP_PERFORMANCE, TOOL_GROUP_PLUGINS, TOOL_GROUP_REASONING,
            TOOL_GROUP_RECRUITMENT, TOOL_GROUP_RESEARCH,
            TOOL_GROUP_WEB,
        )

        def _want(group: str) -> bool:
            """Check if a tool group is requested (or if we're in unfiltered mode)."""
            return tool_groups is None or group in tool_groups

        # Memory is handled by the pre/post pipeline (local LLM), not agent tools
        tools: list[dict[str, Any]] = []

        if _want(TOOL_GROUP_DELEGATION) and self.config.delegation.can_delegate_to:
            tools.extend(DELEGATION_TOOLS)

        if _want(TOOL_GROUP_REASONING) and self.reasoning_engine:
            from axon.reasoning.tools import REASONING_TOOLS
            tools.extend(REASONING_TOOLS)

        if _want(TOOL_GROUP_COMMS) and self._comms_executor:
            from axon.comms.tools import COMMS_TOOLS
            tools.extend(COMMS_TOOLS)

        if _want(TOOL_GROUP_WEB) and self._web_executor:
            from axon.web.tools import WEB_TOOLS
            tools.extend(WEB_TOOLS)

        if _want(TOOL_GROUP_RESEARCH) and self._web_executor:
            from axon.research.tools import RESEARCH_TOOLS
            tools.extend(RESEARCH_TOOLS)

        if _want(TOOL_GROUP_BROWSER) and self._browser_executor:
            from axon.browser.tools import BROWSER_TOOLS
            tools.extend(BROWSER_TOOLS)

        if _want(TOOL_GROUP_MEDIA) and self._media_executor:
            from axon.media.tools import MEDIA_TOOLS
            tools.extend(MEDIA_TOOLS)

        if tool_groups is None and self._integration_executor:
            tools.extend(self._integration_executor.get_tools())

        # Plugin tools
        if _want(TOOL_GROUP_PLUGINS) and self._plugin_executor:
            tools.extend(self._plugin_executor.tools)

        if _want(TOOL_GROUP_DISCOVERY):
            tools.extend(DISCOVERY_TOOLS)
            tools.extend(CAPABILITY_TOOLS)

        if _want(TOOL_GROUP_RECRUITMENT):
            tools.extend(RECRUITMENT_TOOLS)

        if self.shared_vault:
            # Tasks handled by pre/post pipeline, not agent tools
            if _want(TOOL_GROUP_ISSUES):
                tools.extend(ISSUE_TOOLS)
            if _want(TOOL_GROUP_KNOWLEDGE):
                tools.extend(KNOWLEDGE_TOOLS)
            if _want(TOOL_GROUP_ORG_SEARCH):
                tools.extend(ORG_SEARCH_TOOLS)
            if _want(TOOL_GROUP_PERFORMANCE):
                tools.extend(PERFORMANCE_TOOLS)

        # Apply guardrail tool restrictions (whitelist/blacklist/action gates)
        if self.config.guardrails.has_tool_restrictions or not self.config.guardrails.actions.can_send:
            tools = self.config.guardrails.filter_tools(tools)

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

            # Drain any stream events emitted during tool execution
            for event in self._pending_tool_events:
                yield event
            self._pending_tool_events.clear()

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

            # Self-regulation: check cumulative risk after each tool call
            if self._regulation_tracker and self._regulation_tracker.record_action():
                yield StreamChunk(
                    agent_id=self.id,
                    type="text",
                    content=(
                        "\n\n**[Self-regulation triggered]** "
                        f"I've executed {self._regulation_tracker.action_count} actions "
                        f"with cumulative risk {self._regulation_tracker.cumulative_risk:.0%}. "
                        "Pausing to check in — should I continue?"
                    ),
                )
                self._regulation_tracker.reset()
                return

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

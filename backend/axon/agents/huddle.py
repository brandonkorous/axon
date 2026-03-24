"""Huddle orchestrator — multi-persona advisory sessions."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, AsyncIterator

from axon.agents.agent import StreamChunk
from axon.agents.provider import stream_completion
from axon.agents.conversation import Conversation, ConversationManager
from axon.agents.shared_tools import SharedVaultToolExecutor, TASK_TOOLS
from axon.config import PersonaConfig
from axon.vault.navigator import MemoryNavigator
from axon.vault.vault import VaultManager

if TYPE_CHECKING:
    from axon.usage import UsageTracker

logger = logging.getLogger(__name__)


# Speaker detection: matches **Name:** or **Name → Name:**
SPEAKER_PATTERN = re.compile(
    r"\*\*(\w+)(?:\s*→\s*(\w+))?\s*:\*\*"
)

# The Table synthesis pattern
TABLE_PATTERN = re.compile(r"\*\*The Table:\*\*")

# @mention detection: matches @name (case-insensitive)
MENTION_PATTERN = re.compile(r"@(\w+)", re.IGNORECASE)

# Mode prefixes that get injected into the user message
MODE_PREFIXES = {
    "standard": "",
    "vote": "Let's vote on this: ",
    "devils_advocate": "Play devil's advocate on this: ",
    "pressure_test": "Pressure test this — each of you attack it from your domain: ",
    "quick_take": "Quick take — one sentence each, no discussion: ",
    "decision": "We need a decision on this: ",
}


@dataclass
class HuddleChunk:
    """A chunk of huddle output tagged with speaker info."""

    speaker: str | None  # "marcus", "raj", "diana", "table", or None (narrative)
    target: str | None  # For "marcus → raj" style messages
    type: str  # "text", "thinking", "done"
    content: str = ""


def split_response_by_speaker(
    text: str, timestamp: float,
) -> list[dict[str, Any]]:
    """Split a stored huddle response into per-speaker segments for history.

    Returns a list of dicts with role, content, speaker, target, timestamp.
    """
    segments: list[dict[str, Any]] = []
    current_speaker: str | None = None
    current_target: str | None = None

    remaining = text
    while remaining:
        speaker_match = SPEAKER_PATTERN.search(remaining)
        table_match = TABLE_PATTERN.search(remaining)

        match = None
        if speaker_match and table_match:
            match = speaker_match if speaker_match.start() < table_match.start() else table_match
        elif speaker_match:
            match = speaker_match
        elif table_match:
            match = table_match

        if match is None:
            # No more tags — emit remaining text with current speaker
            if remaining.strip():
                segments.append({
                    "role": "assistant",
                    "content": remaining.strip(),
                    "speaker": current_speaker,
                    "target": current_target,
                    "timestamp": timestamp,
                })
            break

        before = remaining[: match.start()]
        if before.strip():
            segments.append({
                "role": "assistant",
                "content": before.strip(),
                "speaker": current_speaker,
                "target": current_target,
                "timestamp": timestamp,
            })

        if match == table_match:
            current_speaker = "table"
            current_target = None
        else:
            current_speaker = match.group(1).lower()
            current_target = match.group(2).lower() if match.group(2) else None

        remaining = remaining[match.end() :]

    # If no segments were created (no tags at all), return the whole text
    if not segments and text.strip():
        segments.append({
            "role": "assistant",
            "content": text.strip(),
            "speaker": None,
            "target": None,
            "timestamp": timestamp,
        })

    return segments


class Huddle:
    """Orchestrates multi-persona huddle sessions.

    Single LLM conversation with the huddle system prompt.
    Parses **Speaker:** prefixes into tagged chunks for the UI.
    """

    def __init__(
        self,
        config: PersonaConfig,
        advisor_configs: dict[str, PersonaConfig],
        data_dir: str = "/data",
        usage_tracker: "UsageTracker | None" = None,
        shared_vault: VaultManager | None = None,
    ):
        self.config = config
        self.advisor_configs = advisor_configs
        self._usage_tracker = usage_tracker

        # Vault access — huddle vault + read-only advisor vaults
        self.vault = VaultManager(config.vault.path, config.vault.root_file)
        self.navigators: dict[str, MemoryNavigator] = {}

        # Build navigators for all accessible vaults
        self.navigators["huddle"] = MemoryNavigator(config.vault.path, config.vault.root_file, cache=self.vault.cache)

        # Dynamically mount all advisor vaults (no need to list them in huddle.yaml)
        for aid, cfg in advisor_configs.items():
            if cfg.vault.path:
                self.navigators[aid] = MemoryNavigator(cfg.vault.path, cfg.vault.root_file)

        # Also mount any explicit read_only_mounts from config (for non-advisor vaults)
        for mount in config.vault.read_only_mounts:
            vault_name = mount.path.rstrip("/").split("/")[-1]
            if vault_name not in self.navigators:
                self.navigators[vault_name] = MemoryNavigator(mount.path, mount.root_file)

        # Conversations (multi-session)
        self.conversation_manager = ConversationManager(agent_id="huddle", data_dir=data_dir)

        # Task tools — allows huddle advisors to create async tasks
        self._shared_executor: SharedVaultToolExecutor | None = None
        self._task_tools: list[dict[str, Any]] | None = None
        if shared_vault:
            self._shared_executor = SharedVaultToolExecutor(
                shared_vault, "huddle",
                conversation_manager=self.conversation_manager,
                ws_target="huddle",
            )
            self._task_tools = TASK_TOOLS

        # System prompt
        self._system_prompt: str | None = None

    def refresh_advisors(self, advisor_configs: dict[str, PersonaConfig]) -> None:
        """Hot-reload advisor roster and vault navigators after team changes."""
        self.advisor_configs = advisor_configs

        # Rebuild navigators: keep huddle + explicit mounts, replace advisor vaults
        refreshed: dict[str, MemoryNavigator] = {
            "huddle": self.navigators["huddle"],
        }
        for aid, cfg in advisor_configs.items():
            if cfg.vault.path:
                refreshed[aid] = MemoryNavigator(cfg.vault.path, cfg.vault.root_file)
        for mount in self.config.vault.read_only_mounts:
            vault_name = mount.path.rstrip("/").split("/")[-1]
            if vault_name not in refreshed:
                refreshed[vault_name] = MemoryNavigator(mount.path, mount.root_file)
        self.navigators = refreshed

        # Clear cached system prompt so roster regenerates on next use
        self._system_prompt = None

    @property
    def conversation(self) -> Conversation:
        """Active conversation (backward-compat with single-conversation code)."""
        return self.conversation_manager.active

    @property
    def system_prompt(self) -> str:
        if self._system_prompt is None:
            raw = self.config.load_system_prompt(self.config.vault.path)
            self._system_prompt = self._inject_roster(raw)
        return self._system_prompt

    def _inject_roster(self, raw: str) -> str:
        """Inject a dynamic advisor roster built from live configs.

        Handles both the {{ADVISOR_ROSTER}} placeholder (template) and
        baked files (replaces the ## The Advisors section entirely).
        """
        roster = self._build_roster()

        # Template placeholder
        if "{{ADVISOR_ROSTER}}" in raw:
            return raw.replace("{{ADVISOR_ROSTER}}", roster)

        # Baked file — replace the section between "## The Advisors" and the next "##"
        pattern = r"(## The Advisors\s*\n).*?(?=\n## )"
        replacement = rf"\g<1>\n{roster}\n"
        result = re.sub(pattern, replacement, raw, count=1, flags=re.DOTALL)
        return result

    def _build_roster(self) -> str:
        """Build the advisor roster section from live advisor configs."""
        lines = []
        for aid, cfg in self.advisor_configs.items():
            lines.append(f'### {cfg.name} — {cfg.title} ("{cfg.tagline}")')
        return "\n\n".join(lines)

    async def process(
        self, user_message: str, mode: str = "standard"
    ) -> AsyncIterator[HuddleChunk]:
        """Process a user message through the huddle."""
        yield HuddleChunk(speaker=None, target=None, type="thinking")

        # Apply mode prefix
        prefix = MODE_PREFIXES.get(mode, "")
        full_message = f"{prefix}{user_message}" if prefix else user_message

        # Detect @mentions and add directive for addressed advisors
        mentions = MENTION_PATTERN.findall(user_message)
        advisor_names = {cfg.name.lower(): cfg.name for cfg in self.advisor_configs.values()}
        addressed = [advisor_names[m.lower()] for m in mentions if m.lower() in advisor_names]
        if addressed:
            names = ", ".join(addressed)
            full_message += (
                f"\n\n[The user is directly addressing {names}. "
                f"{names} should respond FIRST and most substantively using the **Name:** format. "
                f"Other advisors may add brief reactions.]"
            )

        # Gather context from all accessible vaults
        vault_context = await self._gather_context(user_message)

        # Build messages
        messages = [
            {"role": "system", "content": self.system_prompt},
        ]

        if vault_context:
            messages.append({
                "role": "system",
                "content": f"## Vault Context\n\n{vault_context}",
            })

        messages.extend(self.conversation.get_llm_messages())
        messages.append({"role": "user", "content": full_message})

        # Save user message
        self.conversation.add_user_message(full_message)

        # Stream response with tool call support
        full_response = ""
        current_speaker: str | None = None
        current_target: str | None = None
        text_buffer = ""
        tool_calls_buffer: dict[int, dict] = {}
        max_tool_rounds = 3

        for _round in range(max_tool_rounds + 1):
            tool_calls_buffer.clear()

            async for chunk in stream_completion(
                model=self.config.model.reasoning,
                messages=messages,
                tools=self._task_tools,
                max_tokens=self.config.model.max_tokens,
                temperature=self.config.model.temperature,
            ):
                if chunk["type"] == "usage":
                    if self._usage_tracker:
                        try:
                            self._usage_tracker.record(
                                model=self.config.model.reasoning,
                                prompt_tokens=chunk.get("prompt_tokens", 0),
                                completion_tokens=chunk.get("completion_tokens", 0),
                                total_tokens=chunk.get("total_tokens", 0),
                                cost=chunk.get("cost", 0.0),
                                agent_id="huddle",
                                call_type="stream",
                                caller="huddle",
                            )
                        except Exception:
                            pass
                    continue

                if chunk["type"] == "tool_call":
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
                    continue

                if chunk["type"] == "finish":
                    if chunk["reason"] == "tool_calls" and tool_calls_buffer:
                        break  # Handle tool calls below
                    continue

                if chunk["type"] != "text":
                    continue

                text_buffer += chunk["content"]
                full_response += chunk["content"]

                # Parse speaker tags from streamed text
                async for hc in self._parse_speaker_chunks(
                    text_buffer, current_speaker, current_target
                ):
                    if hc.type == "_buffer":
                        text_buffer = hc.content
                        current_speaker = hc.speaker
                        current_target = hc.target
                    else:
                        current_speaker = hc.speaker
                        current_target = hc.target
                        yield hc

            # If no tool calls, we're done streaming
            if not tool_calls_buffer:
                break

            # Execute tool calls and continue conversation
            await self._execute_tool_calls(messages, tool_calls_buffer, full_response)

        # Flush remaining buffer
        if text_buffer.strip():
            yield HuddleChunk(
                speaker=current_speaker,
                target=current_target,
                type="text",
                content=text_buffer,
            )

        # Save to history
        if full_response:
            self.conversation.add_assistant_message(full_response, agent_id="huddle")

        yield HuddleChunk(speaker=None, target=None, type="done")

    async def _parse_speaker_chunks(
        self,
        text_buffer: str,
        current_speaker: str | None,
        current_target: str | None,
    ) -> AsyncIterator[HuddleChunk]:
        """Parse speaker tags from the text buffer, yielding tagged chunks.

        Yields HuddleChunk for text content and a special _buffer chunk
        with the remaining unparsed text.
        """
        while True:
            speaker_match = SPEAKER_PATTERN.search(text_buffer)
            table_match = TABLE_PATTERN.search(text_buffer)

            match = None
            if speaker_match and table_match:
                match = speaker_match if speaker_match.start() < table_match.start() else table_match
            elif speaker_match:
                match = speaker_match
            elif table_match:
                match = table_match

            if match is None:
                if len(text_buffer) > 20:
                    emit = text_buffer[:-20]
                    text_buffer = text_buffer[-20:]
                    if emit:
                        yield HuddleChunk(
                            speaker=current_speaker,
                            target=current_target,
                            type="text",
                            content=emit,
                        )
                break

            before = text_buffer[:match.start()]
            if before.strip():
                yield HuddleChunk(
                    speaker=current_speaker,
                    target=current_target,
                    type="text",
                    content=before,
                )

            if match == table_match:
                current_speaker = "table"
                current_target = None
            else:
                current_speaker = match.group(1).lower()
                current_target = match.group(2).lower() if match.group(2) else None

            text_buffer = text_buffer[match.end():]

        # Return remaining buffer as a special chunk
        yield HuddleChunk(speaker=current_speaker, target=current_target, type="_buffer", content=text_buffer)

    async def _execute_tool_calls(
        self,
        messages: list[dict[str, Any]],
        tool_calls: dict[int, dict],
        response_so_far: str,
    ) -> None:
        """Execute buffered tool calls and append results to messages."""
        if not self._shared_executor:
            return

        # Build assistant message with tool_calls
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

        messages.append({
            "role": "assistant",
            "content": response_so_far or None,
            "tool_calls": tool_call_objects,
        })

        for tc_data in tool_calls.values():
            try:
                result = await self._shared_executor.execute(
                    tc_data["function"], tc_data["arguments"],
                )
            except Exception as e:
                result = f"Error: {e}"
                logger.exception("Huddle tool call failed: %s", tc_data["function"])

            messages.append({
                "role": "tool",
                "tool_call_id": tc_data["id"],
                "content": result,
            })

    async def _gather_context(self, query: str) -> str:
        """Gather relevant context from all accessible vaults."""
        sections: list[str] = []
        tokens_per_vault = 1000  # Split budget across vaults

        for name, navigator in self.navigators.items():
            context = await navigator.retrieve(query, token_budget=tokens_per_vault)
            if context and context != "*No relevant vault context found.*":
                sections.append(f"### {name.title()} Vault\n{context}")

        return "\n\n---\n\n".join(sections) if sections else ""

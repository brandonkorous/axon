"""Huddle orchestrator — multi-agent advisory sessions.

Instead of a single LLM pretending to be multiple advisors, the huddle
fans out user messages to real Agent instances sequentially.  Each advisor
responds with their own tools, vault, and memory.  A lightweight "Table"
synthesis pass runs at the end to tie everything together.
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, AsyncIterator

from axon.agents.provider import stream_completion
from axon.agents.conversation import Conversation, ConversationManager
from axon.config import PersonaConfig
from axon.vault.navigator import MemoryNavigator
from axon.vault.vault import VaultManager

if TYPE_CHECKING:
    from axon.agents.agent import Agent
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
    """Orchestrates multi-agent huddle sessions.

    Fans out user messages to real Agent instances, collects their responses
    (with full tool-calling support), then runs a Table synthesis pass.
    """

    def __init__(
        self,
        config: PersonaConfig,
        advisor_configs: dict[str, PersonaConfig],
        data_dir: str = "/data",
        usage_tracker: "UsageTracker | None" = None,
        shared_vault: VaultManager | None = None,
        org_id: str = "",
        advisor_agents: dict[str, "Agent"] | None = None,
    ):
        self.config = config
        self.advisor_configs = advisor_configs
        self.advisor_agents: dict[str, "Agent"] = advisor_agents or {}
        self._usage_tracker = usage_tracker

        # Vault access — huddle vault + read-only advisor vaults
        self.vault = VaultManager(config.vault.path, config.vault.root_file)
        self.navigators: dict[str, MemoryNavigator] = {}

        self.navigators["huddle"] = MemoryNavigator(
            config.vault.path, config.vault.root_file, cache=self.vault.cache,
        )

        for aid, cfg in advisor_configs.items():
            if cfg.vault.path:
                self.navigators[aid] = MemoryNavigator(cfg.vault.path, cfg.vault.root_file)

        for mount in config.vault.read_only_mounts:
            vault_name = mount.path.rstrip("/").split("/")[-1]
            if vault_name not in self.navigators:
                self.navigators[vault_name] = MemoryNavigator(mount.path, mount.root_file)

        # Conversations (multi-session)
        self.conversation_manager = ConversationManager(agent_id="huddle", data_dir=data_dir)

    def refresh_advisors(
        self,
        advisor_configs: dict[str, PersonaConfig],
        advisor_agents: dict[str, "Agent"] | None = None,
    ) -> None:
        """Hot-reload advisor roster and vault navigators after team changes."""
        self.advisor_configs = advisor_configs
        if advisor_agents is not None:
            self.advisor_agents = advisor_agents

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

    @property
    def conversation(self) -> Conversation:
        """Active conversation (backward-compat with single-conversation code)."""
        return self.conversation_manager.active

    async def process(
        self, user_message: str, mode: str = "standard",
    ) -> AsyncIterator[HuddleChunk]:
        """Orchestrate a huddle round: fan out to advisors, then synthesize."""
        yield HuddleChunk(speaker=None, target=None, type="thinking")

        # Apply mode prefix
        prefix = MODE_PREFIXES.get(mode, "")
        full_message = f"{prefix}{user_message}" if prefix else user_message

        # Detect @mentions for advisor ordering
        mentions = MENTION_PATTERN.findall(user_message)
        name_to_id = {
            cfg.name.lower(): aid for aid, cfg in self.advisor_configs.items()
        }
        addressed_ids = [
            name_to_id[m.lower()] for m in mentions if m.lower() in name_to_id
        ]

        # Order: mentioned advisors first, then the rest
        advisor_order = list(addressed_ids)
        for aid in self.advisor_agents:
            if aid not in advisor_order:
                advisor_order.append(aid)

        # Gather vault context once for all advisor prompts
        vault_context = await self._gather_context(user_message)

        # Save user message to huddle history
        self.conversation.add_user_message(full_message)

        # Phase 1: Fan out to each advisor sequentially
        advisor_responses: dict[str, str] = {}

        for advisor_id in advisor_order:
            agent = self.advisor_agents.get(advisor_id)
            if not agent:
                continue

            cfg = self.advisor_configs.get(advisor_id)
            advisor_name = cfg.name if cfg else advisor_id

            # Build huddle-scoped prompt
            prompt = self._build_advisor_prompt(
                advisor_id, advisor_name, full_message,
                vault_context, advisor_responses,
                is_addressed=(advisor_id in addressed_ids),
                mode=mode,
            )

            # Stream advisor response as HuddleChunks
            advisor_text = ""
            try:
                async for chunk in self._call_advisor(agent, prompt):
                    advisor_text += chunk
                    yield HuddleChunk(
                        speaker=advisor_id, target=None,
                        type="text", content=chunk,
                    )
            except Exception:
                logger.exception("[HUDDLE] Advisor %s failed", advisor_id)
                fallback = f"*[{advisor_name} is unavailable]*\n\n"
                advisor_text = fallback
                yield HuddleChunk(
                    speaker=advisor_id, target=None,
                    type="text", content=fallback,
                )

            # Strip self-attribution if the LLM prefixed with its own name
            advisor_text = re.sub(
                rf"^\s*\*\*{re.escape(advisor_name)}:\*\*\s*",
                "", advisor_text,
            )
            advisor_responses[advisor_id] = advisor_text
            # Save each advisor's response as its own message
            self.conversation.add_assistant_message(advisor_text, agent_id=advisor_id)

        # Phase 2: Table synthesis
        table_text = ""
        async for chunk in self._synthesize_table(full_message, advisor_responses):
            table_text += chunk
            yield HuddleChunk(
                speaker="table", target=None,
                type="text", content=chunk,
            )

        # Save table synthesis as its own message
        if table_text:
            self.conversation.add_assistant_message(table_text, agent_id="table")

        # Fire-and-forget: ingest huddle conclusions into reasoning graph
        if advisor_responses:
            combined = "\n\n".join(
                f"**{self.advisor_configs[aid].name}:**\n{resp}"
                for aid, resp in advisor_responses.items()
                if aid in self.advisor_configs
            )
            if table_text:
                combined += f"\n\n**The Table:**\n{table_text}"
            self._ingest_into_reasoning(combined, full_message)

        yield HuddleChunk(speaker=None, target=None, type="done")

    def _build_advisor_prompt(
        self,
        advisor_id: str,
        advisor_name: str,
        user_message: str,
        vault_context: str,
        prior_responses: dict[str, str],
        is_addressed: bool,
        mode: str = "standard",
    ) -> str:
        """Build the prompt an advisor sees during a huddle turn."""
        parts = [
            f"[HUDDLE SESSION] You are participating in a team huddle as {advisor_name}. "
            f"Respond ONLY as yourself. Do NOT write dialogue for other advisors or "
            f"prefix your response with your name. Do NOT simulate a roundtable — "
            f"just give your own perspective. Keep it concise (2-4 sentences). "
            f"If you need to take action (share knowledge, create tasks, save to vault, "
            f"request new team members via `request_agent`), "
            f"use your tools directly — don't just say you'll do it.",
        ]

        if mode == "vote":
            parts.append("State your position (for/against/conditional) with one-sentence reasoning.")
        elif mode == "devils_advocate":
            parts.append("Argue AGAINST the proposed idea from your domain.")
        elif mode == "pressure_test":
            parts.append("Attack this from your domain — find the weaknesses.")
        elif mode == "quick_take":
            parts.append("One sentence only, no discussion.")
        elif mode == "decision":
            parts.append("State your recommendation clearly with brief reasoning.")

        if prior_responses:
            parts.append("\n**Other advisors have said:**")
            for aid, resp in prior_responses.items():
                cfg = self.advisor_configs.get(aid)
                name = cfg.name if cfg else aid
                # Truncate long responses in context
                summary = resp[:500] + "..." if len(resp) > 500 else resp
                parts.append(f"- **{name}:** {summary}")
            parts.append(
                "\nYou may reference their points, but respond only as yourself."
            )

        if is_addressed:
            parts.append(
                "\nYou were directly @mentioned — respond substantively and first."
            )

        if vault_context:
            parts.append(f"\n**Shared context:**\n{vault_context}")

        parts.append(f"\n**User says:** {user_message}")

        return "\n".join(parts)

    async def _call_advisor(
        self, agent: "Agent", prompt: str,
    ) -> AsyncIterator[str]:
        """Call an advisor agent and yield text chunks.

        Uses agent.process(save_history=False) so huddle exchanges
        don't pollute the advisor's direct chat history. Tool calls
        execute normally within the agent's turn.
        """
        async for chunk in agent.process(prompt, save_history=False):
            if chunk.type == "text":
                yield chunk.content
            # tool_use, tool_result, thinking — handled internally by agent

    async def _synthesize_table(
        self,
        user_message: str,
        advisor_responses: dict[str, str],
    ) -> AsyncIterator[str]:
        """Stream the Table synthesis from advisor responses."""
        messages = self._build_table_messages(user_message, advisor_responses)

        async for chunk in stream_completion(
            model=self.config.model.reasoning,
            messages=messages,
            max_tokens=500,
            temperature=self.config.model.temperature,
        ):
            if chunk["type"] == "text":
                yield chunk["content"]
            elif chunk["type"] == "usage" and self._usage_tracker:
                try:
                    self._usage_tracker.record(
                        model=self.config.model.reasoning,
                        prompt_tokens=chunk.get("prompt_tokens", 0),
                        completion_tokens=chunk.get("completion_tokens", 0),
                        total_tokens=chunk.get("total_tokens", 0),
                        cost=chunk.get("cost", 0.0),
                        agent_id="huddle",
                        call_type="stream",
                        caller="table_synthesis",
                    )
                except Exception:
                    pass

    def _build_table_messages(
        self,
        user_message: str,
        advisor_responses: dict[str, str],
    ) -> list[dict[str, str]]:
        """Build messages for the Table synthesis LLM call."""
        advisor_summary = "\n\n".join(
            f"**{self.advisor_configs[aid].name}:** {resp}"
            for aid, resp in advisor_responses.items()
            if aid in self.advisor_configs
        )

        return [
            {
                "role": "system",
                "content": (
                    "You are 'The Table' — a neutral facilitator synthesizing "
                    "advisor perspectives in a huddle session. Provide a concise "
                    "synthesis (3-5 sentences): where do they agree? Where's the "
                    "tension? What's the recommended path forward? Be direct and "
                    "actionable. Do not repeat what each advisor said — synthesize."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"**Topic:** {user_message}\n\n"
                    f"**Advisor responses:**\n\n{advisor_summary}"
                ),
            },
        ]

    def _ingest_into_reasoning(self, transcript: str, topic: str) -> None:
        """Fire-and-forget: feed huddle conclusions to any advisor's reasoning engine."""
        for agent in self.advisor_agents.values():
            if hasattr(agent, "reasoning_engine") and agent.reasoning_engine:
                asyncio.create_task(
                    agent.reasoning_engine.ingest_huddle_conclusion(transcript, topic)
                )
                break  # Only ingest once — into the first agent with reasoning

    async def _gather_context(self, query: str) -> str:
        """Gather relevant context from all accessible vaults."""
        sections: list[str] = []
        tokens_per_vault = 1000

        for name, navigator in self.navigators.items():
            context = await navigator.retrieve(query, token_budget=tokens_per_vault)
            if context and context != "*No relevant vault context found.*":
                sections.append(f"### {name.title()} Vault\n{context}")

        return "\n\n---\n\n".join(sections) if sections else ""

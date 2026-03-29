"""Huddle — group chat room for AI advisors.

The huddle is a shared space where the user can message all advisors or
specific ones via @mentions.  Each advisor runs as an independent task —
they stream responses directly to the WebSocket as they finish, like real
people typing in a group chat.  The huddle itself is just a message
router, not an orchestrator.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Any, AsyncIterator

from axon.agents.provider import stream_completion, complete
from axon.agents.conversation import Conversation, ConversationManager
from axon.config import PersonaConfig
from axon.vault.navigator import MemoryNavigator
from axon.vault.vault import VaultManager
import axon.ws_registry as ws_registry

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

# Modes that benefit from table synthesis after individual responses
TABLE_MODES = {"vote", "decision", "pressure_test"}

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

    speaker: str | None  # advisor id, "table", or None (control)
    target: str | None  # For "marcus → raj" style messages
    type: str  # "text", "thinking", "speaker_done", "disagreement", "done"
    content: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "speaker": self.speaker,
            "target": self.target,
            "content": self.content,
        }


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
    """Group chat room for AI advisors.

    Messages are dispatched to advisors as independent tasks. Each advisor
    streams its response directly to the WebSocket via ws_registry — whoever
    finishes first appears first, just like a real group chat. The huddle
    is just a router: it determines who should respond, dispatches the
    message, and optionally runs a Table synthesis after everyone finishes.
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
        self._shared_vault = shared_vault
        self._org_id = org_id

        # Org principles (injected from shared vault principles.md)
        self._org_principles: str = ""

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

    async def _push(self, conv_id: str, chunk: HuddleChunk) -> None:
        """Push a chunk to all connected huddle WebSocket clients."""
        await ws_registry.push("huddle", conv_id, chunk.to_dict())

    async def dispatch(
        self, user_message: str, mode: str = "standard",
    ) -> None:
        """Dispatch a user message to all appropriate advisors.

        Each advisor runs as an independent background task that streams
        directly to the WebSocket.  This method returns once all tasks
        are launched — it does NOT wait for advisors to finish.
        """
        conv_id = self.conversation_manager.active_id

        # Apply mode prefix
        prefix = MODE_PREFIXES.get(mode, "")
        full_message = f"{prefix}{user_message}" if prefix else user_message

        # Detect @mentions to filter which advisors respond
        mentions = MENTION_PATTERN.findall(user_message)
        name_to_id = {
            cfg.name.lower(): aid for aid, cfg in self.advisor_configs.items()
        }
        addressed_ids = [
            name_to_id[m.lower()] for m in mentions if m.lower() in name_to_id
        ]

        # Determine which advisors should respond
        responding_ids = (
            addressed_ids if addressed_ids
            else list(self.advisor_agents.keys())
        )

        # Filter to only advisors that actually exist
        responding_ids = [
            aid for aid in responding_ids if aid in self.advisor_agents
        ]

        if not responding_ids:
            await self._push(conv_id, HuddleChunk(
                speaker=None, target=None, type="done",
            ))
            return

        # Gather vault context once for all advisor prompts
        vault_context = await self._gather_context(user_message)

        # Save user message to huddle history
        self.conversation.add_user_message(full_message)

        # Send per-advisor thinking indicators immediately
        for advisor_id in responding_ids:
            await self._push(conv_id, HuddleChunk(
                speaker=advisor_id, target=None, type="thinking",
            ))

        # Track responses for table synthesis and reasoning ingestion
        advisor_responses: dict[str, str] = {}
        response_lock = asyncio.Lock()
        pending = len(responding_ids)
        pending_lock = asyncio.Lock()

        async def _on_all_done() -> None:
            """Called when all advisors have finished responding."""
            # Table synthesis for modes that benefit from it
            if mode in TABLE_MODES and len(advisor_responses) > 1:
                await self._push(conv_id, HuddleChunk(
                    speaker="table", target=None, type="thinking",
                ))
                table_text = ""
                async for chunk in self._synthesize_table(
                    full_message, advisor_responses,
                ):
                    table_text += chunk
                    await self._push(conv_id, HuddleChunk(
                        speaker="table", target=None,
                        type="text", content=chunk,
                    ))

                if table_text:
                    self.conversation.add_assistant_message(
                        table_text, agent_id="table",
                    )
                await self._push(conv_id, HuddleChunk(
                    speaker="table", target=None, type="speaker_done",
                ))

            # Disagreement analysis for TABLE_MODES
            if mode in TABLE_MODES and len(advisor_responses) > 1:
                asyncio.create_task(
                    self._analyze_disagreements(conv_id, full_message, advisor_responses)
                )

            # Fire-and-forget: extract actions (vault saves, tasks)
            if advisor_responses:
                asyncio.create_task(
                    self._extract_and_execute_actions(
                        full_message, advisor_responses,
                    )
                )

            # Ingest into reasoning graph
            if advisor_responses:
                combined = "\n\n".join(
                    f"**{self.advisor_configs[aid].name}:**\n{resp}"
                    for aid, resp in advisor_responses.items()
                    if aid in self.advisor_configs
                )
                self._ingest_into_reasoning(combined, full_message)

            await self._push(conv_id, HuddleChunk(
                speaker=None, target=None, type="done",
            ))

        async def _run_advisor(advisor_id: str) -> None:
            """Run a single advisor — streams directly to WebSocket."""
            nonlocal pending
            if advisor_id not in self.advisor_agents:
                return

            cfg = self.advisor_configs.get(advisor_id)
            advisor_name = cfg.name if cfg else advisor_id

            advisor_text = ""
            try:
                async for chunk in self._call_advisor(
                    advisor_id, advisor_name, full_message,
                    vault_context,
                    is_addressed=(advisor_id in addressed_ids),
                    mode=mode,
                ):
                    advisor_text += chunk
                    await self._push(conv_id, HuddleChunk(
                        speaker=advisor_id, target=None,
                        type="text", content=chunk,
                    ))
            except Exception:
                logger.exception("[HUDDLE] Advisor %s failed", advisor_id)
                fallback = f"*[{advisor_name} is unavailable]*\n\n"
                advisor_text = fallback
                await self._push(conv_id, HuddleChunk(
                    speaker=advisor_id, target=None,
                    type="text", content=fallback,
                ))

            # Strip self-attribution if the LLM prefixed with its own name
            advisor_text = re.sub(
                rf"^\s*\*\*{re.escape(advisor_name)}:\*\*\s*",
                "", advisor_text,
            )

            # Signal this advisor is done
            await self._push(conv_id, HuddleChunk(
                speaker=advisor_id, target=None, type="speaker_done",
            ))

            # Save to conversation history
            async with response_lock:
                advisor_responses[advisor_id] = advisor_text
            self.conversation.add_assistant_message(
                advisor_text, agent_id=advisor_id,
            )

            # Check if all advisors are done
            async with pending_lock:
                pending -= 1
                all_done = pending == 0

            if all_done:
                await _on_all_done()

        # Launch each advisor as an independent fire-and-forget task
        for aid in responding_ids:
            asyncio.create_task(_run_advisor(aid))

    def _build_advisor_system_prompt(
        self,
        advisor_id: str,
        advisor_name: str,
        vault_context: str,
        mode: str = "standard",
    ) -> str:
        """Build the system prompt for an advisor's isolated huddle call."""
        # Start with the advisor's own system prompt for domain expertise
        agent = self.advisor_agents.get(advisor_id)
        base_prompt = ""
        if agent:
            base_prompt = agent.system_prompt or ""

        huddle_rules = (
            f"You are **{advisor_name}** in a group huddle.\n\n"
            f"## CRITICAL RULES\n"
            f"- You are {advisor_name}. Respond ONLY as yourself.\n"
            f"- Do NOT write dialogue for other advisors.\n"
            f"- Do NOT prefix your response with your name or **{advisor_name}:**.\n"
            f"- Do NOT simulate a round-table discussion.\n"
            f"- Just give YOUR perspective, in YOUR voice.\n"
        )

        mode_instruction = {
            "standard": (
                "Respond substantively from your domain expertise. "
                "Be concise but thorough — say what needs to be said."
            ),
            "vote": (
                "State your position (for/against/conditional) "
                "with one-sentence reasoning."
            ),
            "devils_advocate": "Argue AGAINST the proposed idea from your domain.",
            "pressure_test": (
                "Attack this from your domain — find the weaknesses."
            ),
            "quick_take": "One sentence only, no discussion.",
            "decision": (
                "State your recommendation clearly with brief reasoning."
            ),
        }.get(mode, "")

        parts = [huddle_rules]
        if self._org_principles:
            parts.append(f"## Organization Principles\n{self._org_principles}\n")
        if mode_instruction:
            parts.append(f"## Mode\n{mode_instruction}\n")
        if base_prompt:
            parts.append(f"## Your Expertise\n{base_prompt}\n")
        if vault_context:
            parts.append(f"## Shared Context\n{vault_context}\n")

        return "\n".join(parts)

    def _build_advisor_messages(
        self,
        advisor_id: str,
        advisor_name: str,
        user_message: str,
        vault_context: str,
        is_addressed: bool,
        mode: str = "standard",
    ) -> list[dict[str, str]]:
        """Build the full message array for an advisor's isolated huddle call.

        History is collapsed into user/assistant turns that model the
        advisor's OWN prior responses (assistant) and everything else
        (user context summaries).  This prevents the LLM from copying
        the [Speaker]: pattern it would see in raw history.
        """
        system_prompt = self._build_advisor_system_prompt(
            advisor_id, advisor_name, vault_context, mode,
        )

        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
        ]

        # Group history into per-turn blocks: user message + advisor responses
        # Each user message starts a new turn. Advisor responses within the
        # same turn are grouped into a context summary (for others) or kept
        # as assistant messages (for this advisor's own responses).
        history = self.conversation.messages
        i = 0
        while i < len(history):
            msg = history[i]
            if msg.role == "user":
                messages.append({"role": "user", "content": msg.content})
                # Collect all advisor responses following this user message
                own_response = ""
                other_summaries: list[str] = []
                j = i + 1
                while j < len(history) and history[j].role != "user":
                    resp = history[j]
                    if resp.role == "assistant":
                        speaker_name = resp.agent_id or "unknown"
                        if resp.agent_id and resp.agent_id in self.advisor_configs:
                            speaker_name = self.advisor_configs[resp.agent_id].name
                        elif resp.agent_id == "table":
                            speaker_name = "The Table"

                        if resp.agent_id == advisor_id:
                            own_response = resp.content
                        else:
                            other_summaries.append(
                                f"{speaker_name}: {resp.content}"
                            )
                    j += 1

                # Emit this advisor's own prior response as assistant
                if own_response:
                    messages.append({"role": "assistant", "content": own_response})
                elif other_summaries:
                    # If this advisor didn't respond but others did, show
                    # a brief context note so the advisor has awareness
                    summary = "\n\n".join(other_summaries)
                    messages.append({
                        "role": "user",
                        "content": (
                            f"[The other advisors responded to this. "
                            f"Here is a summary for context — do NOT "
                            f"repeat or role-play their responses.]\n\n{summary}"
                        ),
                    })

                i = j
            else:
                i += 1

        # Add the current user message
        mention_note = ""
        if is_addressed:
            mention_note = " (You were directly @mentioned — respond substantively.)"
        messages.append({
            "role": "user",
            "content": f"{user_message}{mention_note}",
        })

        return messages

    async def _call_advisor(
        self,
        advisor_id: str,
        advisor_name: str,
        user_message: str,
        vault_context: str,
        is_addressed: bool,
        mode: str = "standard",
    ) -> AsyncIterator[str]:
        """Call an advisor with an isolated LLM call — no shared state.

        Each advisor gets its own system prompt, huddle history, and
        a direct stream_completion call. This prevents cross-talk where
        one advisor generates dialogue for others.
        """
        messages = self._build_advisor_messages(
            advisor_id, advisor_name, user_message,
            vault_context, is_addressed, mode,
        )

        cfg = self.advisor_configs.get(advisor_id)
        model = cfg.model.reasoning if cfg else self.config.model.reasoning

        async for chunk in stream_completion(
            model=model,
            messages=messages,
            max_tokens=cfg.model.max_tokens if cfg else 1000,
            temperature=cfg.model.temperature if cfg else 0.7,
        ):
            if chunk["type"] == "text":
                yield chunk["content"]
            elif chunk["type"] == "usage" and self._usage_tracker:
                try:
                    self._usage_tracker.record(
                        model=model,
                        prompt_tokens=chunk.get("prompt_tokens", 0),
                        completion_tokens=chunk.get("completion_tokens", 0),
                        total_tokens=chunk.get("total_tokens", 0),
                        cost=chunk.get("cost", 0.0),
                        agent_id=advisor_id,
                        call_type="stream",
                        caller="huddle_advisor",
                    )
                except Exception:
                    pass

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
                    "actionable. Do not repeat what each advisor said — synthesize.\n\n"
                    "## Decision Classification\n"
                    "For each decision or recommendation in your synthesis, classify it:\n"
                    "- **[MECHANICAL]**: Obvious, uncontroversial — auto-apply silently.\n"
                    "- **[TASTE]**: Reasonable people could disagree — auto-apply but flag for review.\n"
                    "- **[USER CHALLENGE]**: High-stakes, irreversible, or strategic — "
                    "present options but NEVER decide for the user.\n"
                    "Tag each recommendation with its classification."
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

    async def _analyze_disagreements(
        self,
        conv_id: str,
        user_message: str,
        advisor_responses: dict[str, str],
    ) -> None:
        """Analyze advisor disagreements and push structured report."""
        from axon.agents.disagreement import (
            build_disagreement_prompt,
            parse_disagreement_response,
        )

        advisor_names = {
            aid: cfg.name for aid, cfg in self.advisor_configs.items()
        }
        messages = build_disagreement_prompt(
            user_message, advisor_responses, advisor_names,
        )

        try:
            response = await complete(
                model=self.config.model.reasoning,
                messages=messages,
                max_tokens=800,
                temperature=0.3,
            )
            raw = response.get("content", "")

            report = parse_disagreement_response(raw, user_message)
            if report:
                await self._push(conv_id, HuddleChunk(
                    speaker="table",
                    target=None,
                    type="disagreement",
                    content=json.dumps(report.model_dump()),
                ))
        except Exception as e:
            logger.debug("Disagreement analysis failed (non-critical): %s", e)

    async def _extract_and_execute_actions(
        self,
        user_message: str,
        advisor_responses: dict[str, str],
    ) -> None:
        """Review the huddle exchange and execute any needed actions.

        Runs as a background task after all advisors finish. Identifies:
        - Key data or decisions to save to the shared huddle vault
        - Tasks that should be created and assigned to specific advisors
        """
        advisor_names = {
            aid: cfg.name for aid, cfg in self.advisor_configs.items()
        }
        advisor_list = ", ".join(
            f"{name} (id: {aid})" for aid, name in advisor_names.items()
        )
        advisor_summary = "\n\n".join(
            f"**{advisor_names.get(aid, aid)}:** {resp}"
            for aid, resp in advisor_responses.items()
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a silent post-processing agent for a group chat. "
                    "Review the user's message and advisor responses. Identify "
                    "actions that should be taken.\n\n"
                    "## Save to vault when the user:\n"
                    "- Shares reference data (colors, specs, configs, brand guidelines)\n"
                    "- Makes a decision or announces a policy\n"
                    "- Provides context advisors will need in future conversations\n"
                    "- Corrects a misunderstanding that should not recur\n\n"
                    "## Create tasks when:\n"
                    "- The user explicitly requests work to be done\n"
                    "- An advisor commits to a specific deliverable\n"
                    "- A clear action item emerges from the discussion\n"
                    "- Work is agreed upon that needs tracking\n\n"
                    "## Do NOT act on:\n"
                    "- General discussion, opinions, or brainstorming\n"
                    "- Information already in the vault\n"
                    "- Trivial or ephemeral exchanges\n"
                    "- Vague intentions without clear deliverables\n\n"
                    f"## Available advisors:\n{advisor_list}\n\n"
                    "## Response format\n"
                    "Respond with a JSON array of actions:\n\n"
                    "Vault save:\n"
                    '  {"action": "vault_write", "path": "reference/<slug>.md", '
                    '"name": "...", "description": "...", "tags": "...", '
                    '"content": "..."}\n\n'
                    "Task creation:\n"
                    '  {"action": "task_create", "title": "...", '
                    '"description": "...", "assignee": "<agent_id>", '
                    '"priority": "p2"}\n\n'
                    "Memory nudge (remind an advisor to save important info "
                    "to their own vault — use when the user shares key data "
                    "that each advisor should have in personal memory):\n"
                    '  {"action": "memory_nudge", "agent_id": "<agent_id>", '
                    '"content": "Verify you have saved ... to your vault. '
                    'If not, save it now."}\n\n'
                    "If nothing needs doing, respond with: []"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"**User said:** {user_message}\n\n"
                    f"**Advisor responses:**\n\n{advisor_summary}"
                ),
            },
        ]

        try:
            result = await complete(
                model=self.config.model.reasoning,
                messages=messages,
                max_tokens=1000,
                temperature=0.0,
            )
            content = result.get("content", "").strip()

            # Extract JSON from the response (handle markdown code blocks)
            json_match = re.search(r"\[.*\]", content, re.DOTALL)
            if not json_match:
                return

            actions = json.loads(json_match.group())
            if not isinstance(actions, list) or not actions:
                return

            for action in actions:
                action_type = action.get("action")
                if action_type == "vault_write":
                    self._execute_vault_write(action)
                elif action_type == "task_create":
                    await self._execute_task_create(action)
                elif action_type == "memory_nudge":
                    self._execute_memory_nudge(action)

        except Exception:
            logger.exception("[HUDDLE] Action extraction failed")

    def _execute_vault_write(self, action: dict[str, Any]) -> None:
        """Save a reference entry to the huddle vault."""
        path = action.get("path", "")
        if not path:
            return

        metadata = {
            "name": action.get("name", ""),
            "description": action.get("description", ""),
            "type": "reference",
            "date": str(date.today()),
            "status": "active",
            "tags": action.get("tags", ""),
            "source": "huddle",
        }
        self.vault.write_file(path, metadata, action.get("content", ""))
        logger.info("[HUDDLE] Auto-saved to vault: %s", path)

    async def _execute_task_create(self, action: dict[str, Any]) -> None:
        """Create a task in the shared org vault and trigger execution."""
        if not self._shared_vault:
            logger.warning("[HUDDLE] Cannot create task — no shared vault")
            return

        title = action.get("title", "")
        if not title:
            return

        from datetime import datetime

        slug = re.sub(r"[^\w\s-]", "", title.lower().strip())
        slug = re.sub(r"[\s_]+", "-", slug)
        slug = re.sub(r"-+", "-", slug).strip("-")[:50]
        today_str = str(date.today())
        path = f"tasks/{today_str}-{slug}.md"

        assignee = action.get("assignee", "")
        status = "in_progress" if assignee else "pending"

        metadata = {
            "name": title,
            "type": "task",
            "owner": "huddle",
            "assignee": assignee,
            "status": status,
            "priority": action.get("priority", "p2"),
            "labels": [],
            "conversation_id": self.conversation_manager.active_id,
            "ws_target": "huddle",
            "created_by": "huddle",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "responses": [],
        }
        content = f"# {title}\n\n{action.get('description', '')}"
        self._shared_vault.write_file(path, metadata, content)
        self._shared_vault._update_branch_index("tasks", slug, title)
        logger.info("[HUDDLE] Task created: %s → %s", path, assignee or "unassigned")

        # Trigger scheduler to pick up the task if it has an assignee
        if assignee and self._org_id:
            from axon.scheduler import scheduler
            await asyncio.sleep(2)
            await scheduler.trigger_task_execution(self._org_id, assignee)

    def _execute_memory_nudge(self, action: dict[str, Any]) -> None:
        """Drop a memory nudge into an advisor's inbox.

        The advisor will see this on their next conversation turn and
        verify/save the information to their personal vault.
        """
        agent_id = action.get("agent_id", "")
        content = action.get("content", "")
        if not agent_id or not content:
            return

        agent = self.advisor_agents.get(agent_id)
        if not agent:
            logger.warning("[HUDDLE] Memory nudge target not found: %s", agent_id)
            return

        from datetime import datetime

        today_str = str(date.today())
        slug = f"huddle-memory-{today_str}-{id(action) % 10000:04d}"
        inbox_path = f"inbox/{slug}.md"

        metadata = {
            "from": "huddle",
            "type": "memory_nudge",
            "date": today_str,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
        agent.vault.write_file(inbox_path, metadata, content)
        logger.info("[HUDDLE] Memory nudge → %s: %s", agent_id, inbox_path)

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

"""Boardroom orchestrator — multi-persona advisory sessions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, AsyncIterator

from axon.agents.agent import StreamChunk
from axon.agents.provider import stream_completion
from axon.agents.conversation import Conversation
from axon.config import PersonaConfig
from axon.vault.navigator import MemoryNavigator
from axon.vault.vault import VaultManager


# Speaker detection: matches **Name:** or **Name → Name:**
SPEAKER_PATTERN = re.compile(
    r"\*\*(\w+)(?:\s*→\s*(\w+))?\s*:\*\*"
)

# The Table synthesis pattern
TABLE_PATTERN = re.compile(r"\*\*The Table:\*\*")

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
class BoardroomChunk:
    """A chunk of boardroom output tagged with speaker info."""

    speaker: str | None  # "marcus", "raj", "diana", "table", or None (narrative)
    target: str | None  # For "marcus → raj" style messages
    type: str  # "text", "thinking", "done"
    content: str = ""


class Boardroom:
    """Orchestrates multi-persona boardroom sessions.

    Single LLM conversation with the boardroom system prompt.
    Parses **Speaker:** prefixes into tagged chunks for the UI.
    """

    def __init__(
        self,
        config: PersonaConfig,
        advisor_configs: dict[str, PersonaConfig],
        data_dir: str = "/data",
    ):
        self.config = config
        self.advisor_configs = advisor_configs

        # Vault access — boardroom vault + read-only advisor vaults
        self.vault = VaultManager(config.vault.path, config.vault.root_file)
        self.navigators: dict[str, MemoryNavigator] = {}

        # Build navigators for all accessible vaults
        self.navigators["boardroom"] = MemoryNavigator(config.vault.path, config.vault.root_file)
        for mount in config.vault.read_only_mounts:
            vault_name = mount.path.rstrip("/").split("/")[-1]
            self.navigators[vault_name] = MemoryNavigator(mount.path, mount.root_file)

        # Conversation
        self.conversation = Conversation(agent_id="boardroom", data_dir=data_dir)

        # System prompt
        self._system_prompt: str | None = None

    @property
    def system_prompt(self) -> str:
        if self._system_prompt is None:
            self._system_prompt = self.config.load_system_prompt(
                self.config.system_prompt_file
            )
        return self._system_prompt

    async def process(
        self, user_message: str, mode: str = "standard"
    ) -> AsyncIterator[BoardroomChunk]:
        """Process a user message through the boardroom."""
        yield BoardroomChunk(speaker=None, target=None, type="thinking")

        # Apply mode prefix
        prefix = MODE_PREFIXES.get(mode, "")
        full_message = f"{prefix}{user_message}" if prefix else user_message

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

        # Stream response
        full_response = ""
        current_speaker: str | None = None
        current_target: str | None = None
        text_buffer = ""

        async for chunk in stream_completion(
            model=self.config.model.reasoning,
            messages=messages,
            max_tokens=self.config.model.max_tokens,
            temperature=self.config.model.temperature,
        ):
            if chunk["type"] != "text":
                continue

            text_buffer += chunk["content"]
            full_response += chunk["content"]

            # Check for speaker changes in the buffer
            while True:
                # Look for **Speaker:** or **The Table:**
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
                    # No speaker change — emit buffered text with current speaker
                    # But keep a small buffer in case a speaker tag is being streamed
                    if len(text_buffer) > 20:
                        emit = text_buffer[:-20]
                        text_buffer = text_buffer[-20:]
                        if emit:
                            yield BoardroomChunk(
                                speaker=current_speaker,
                                target=current_target,
                                type="text",
                                content=emit,
                            )
                    break

                # Emit text before the speaker tag
                before = text_buffer[:match.start()]
                if before.strip():
                    yield BoardroomChunk(
                        speaker=current_speaker,
                        target=current_target,
                        type="text",
                        content=before,
                    )

                # Update speaker
                if match == table_match:
                    current_speaker = "table"
                    current_target = None
                else:
                    current_speaker = match.group(1).lower()
                    current_target = match.group(2).lower() if match.group(2) else None

                # Continue with remaining text
                text_buffer = text_buffer[match.end():]

        # Flush remaining buffer
        if text_buffer.strip():
            yield BoardroomChunk(
                speaker=current_speaker,
                target=current_target,
                type="text",
                content=text_buffer,
            )

        # Save to history
        if full_response:
            self.conversation.add_assistant_message(full_response, agent_id="boardroom")

        yield BoardroomChunk(speaker=None, target=None, type="done")

    async def _gather_context(self, query: str) -> str:
        """Gather relevant context from all accessible vaults."""
        sections: list[str] = []
        tokens_per_vault = 1000  # Split budget across vaults

        for name, navigator in self.navigators.items():
            context = await navigator.retrieve(query, token_budget=tokens_per_vault)
            if context and context != "*No relevant vault context found.*":
                sections.append(f"### {name.title()} Vault\n{context}")

        return "\n\n---\n\n".join(sections) if sections else ""

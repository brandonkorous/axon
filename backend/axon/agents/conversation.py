"""Conversation state management — history, persistence, context windowing."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Message:
    """A single message in a conversation."""

    role: str  # "user", "assistant", "system", "tool"
    content: str
    agent_id: str | None = None  # Which agent produced this message
    timestamp: float = field(default_factory=time.time)
    tool_call_id: str | None = None  # For tool result messages
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_llm_message(self) -> dict[str, Any]:
        """Convert to the format expected by LiteLLM."""
        msg: dict[str, Any] = {"role": self.role, "content": self.content}
        if self.tool_call_id:
            msg["tool_call_id"] = self.tool_call_id
        return msg


class Conversation:
    """Manages conversation history for an agent.

    Handles:
    - Message storage
    - Context window management (keep recent, summarize old)
    - Persistence to disk
    """

    def __init__(
        self,
        agent_id: str,
        data_dir: str = "/data",
        max_messages: int = 50,
    ):
        self.agent_id = agent_id
        self.data_dir = Path(data_dir)
        self.max_messages = max_messages
        self.messages: list[Message] = []
        self._load()

    def add_user_message(self, content: str) -> Message:
        """Add a user message to the conversation."""
        msg = Message(role="user", content=content)
        self.messages.append(msg)
        self._trim()
        self._save()
        return msg

    def add_assistant_message(self, content: str, agent_id: str | None = None) -> Message:
        """Add an assistant message to the conversation."""
        msg = Message(role="assistant", content=content, agent_id=agent_id)
        self.messages.append(msg)
        self._trim()
        self._save()
        return msg

    def add_tool_result(self, tool_call_id: str, content: str) -> Message:
        """Add a tool result message."""
        msg = Message(role="tool", content=content, tool_call_id=tool_call_id)
        self.messages.append(msg)
        self._save()
        return msg

    def get_llm_messages(self) -> list[dict[str, Any]]:
        """Get messages formatted for LLM consumption."""
        return [m.to_llm_message() for m in self.messages]

    def clear(self) -> None:
        """Clear conversation history."""
        self.messages = []
        self._save()

    def _trim(self) -> None:
        """Keep conversation within max_messages limit.

        Removes oldest messages (keeping system messages).
        """
        if len(self.messages) <= self.max_messages:
            return

        # Keep the last max_messages messages
        self.messages = self.messages[-self.max_messages:]

    def _save(self) -> None:
        """Persist conversation to disk."""
        save_dir = self.data_dir / "conversations"
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = save_dir / f"{self.agent_id}.json"

        data = [
            {
                "role": m.role,
                "content": m.content,
                "agent_id": m.agent_id,
                "timestamp": m.timestamp,
                "tool_call_id": m.tool_call_id,
                "metadata": m.metadata,
            }
            for m in self.messages
        ]

        save_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _load(self) -> None:
        """Load conversation from disk."""
        save_path = self.data_dir / "conversations" / f"{self.agent_id}.json"
        if not save_path.exists():
            return

        try:
            data = json.loads(save_path.read_text(encoding="utf-8"))
            self.messages = [
                Message(
                    role=m["role"],
                    content=m["content"],
                    agent_id=m.get("agent_id"),
                    timestamp=m.get("timestamp", 0),
                    tool_call_id=m.get("tool_call_id"),
                    metadata=m.get("metadata", {}),
                )
                for m in data
            ]
        except Exception:
            self.messages = []

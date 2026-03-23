"""Conversation state management — history, persistence, context windowing."""

from __future__ import annotations

import json
import logging
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("axon.conversation")


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
        conversation_id: str | None = None,
    ):
        self.agent_id = agent_id
        self.conversation_id = conversation_id
        self.data_dir = Path(data_dir)
        self.max_messages = max_messages
        self.messages: list[Message] = []
        self._load()

    @property
    def _save_path(self) -> Path:
        """Resolve the file path for this conversation."""
        if self.conversation_id:
            return self.data_dir / "conversations" / self.agent_id / f"{self.conversation_id}.json"
        return self.data_dir / "conversations" / f"{self.agent_id}.json"

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
        save_path = self._save_path
        save_path.parent.mkdir(parents=True, exist_ok=True)

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
        save_path = self._save_path
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


# ---------------------------------------------------------------------------
# ConversationManager — manages multiple conversations per agent
# ---------------------------------------------------------------------------

TITLE_MAX_LENGTH = 60


@dataclass
class ConversationMeta:
    """Index entry for a conversation."""

    id: str
    title: str
    created_at: float
    last_message_at: float
    message_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at,
            "last_message_at": self.last_message_at,
            "message_count": self.message_count,
        }


class ConversationManager:
    """Manages multiple conversations for a single agent/huddle."""

    def __init__(
        self,
        agent_id: str,
        data_dir: str = "/data",
        max_messages: int = 50,
    ):
        self.agent_id = agent_id
        self.data_dir = Path(data_dir)
        self.max_messages = max_messages
        self.conversations_dir = self.data_dir / "conversations" / agent_id
        self.conversations_dir.mkdir(parents=True, exist_ok=True)

        self._migrate_legacy()
        self._index: list[ConversationMeta] = []
        self._active_id: str = ""
        self._load_index()

        # Ensure at least one conversation exists
        if not self._index:
            self.create_new()
        elif not self._active_id:
            self._active_id = self._index[0].id

        self._active: Conversation = Conversation(
            agent_id=self.agent_id,
            data_dir=str(self.data_dir),
            max_messages=self.max_messages,
            conversation_id=self._active_id,
        )

    @property
    def active(self) -> Conversation:
        """The currently active conversation."""
        return self._active

    @property
    def active_id(self) -> str:
        return self._active_id

    def create_new(self, title: str = "New conversation") -> str:
        """Create a new conversation and set it as active. Returns the conversation ID."""
        now = time.time()
        conv_id = f"{self.agent_id}_{int(now * 1000)}"

        meta = ConversationMeta(
            id=conv_id,
            title=title,
            created_at=now,
            last_message_at=now,
            message_count=0,
        )
        self._index.insert(0, meta)
        self._active_id = conv_id
        self._save_index()

        # Create the new conversation (empty)
        self._active = Conversation(
            agent_id=self.agent_id,
            data_dir=str(self.data_dir),
            max_messages=self.max_messages,
            conversation_id=conv_id,
        )
        return conv_id

    def switch(self, conversation_id: str) -> Conversation:
        """Switch to a different conversation. Raises ValueError if not found."""
        meta = self._find_meta(conversation_id)
        if not meta:
            raise ValueError(f"Conversation not found: {conversation_id}")

        self._active_id = conversation_id
        self._save_index()

        self._active = Conversation(
            agent_id=self.agent_id,
            data_dir=str(self.data_dir),
            max_messages=self.max_messages,
            conversation_id=conversation_id,
        )
        return self._active

    def list_conversations(self) -> list[dict[str, Any]]:
        """List all conversations, most recent first."""
        # Refresh message counts / last_message_at from active conversation
        self._sync_active_meta()
        return [m.to_dict() for m in self._index]

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation. Returns False if not found."""
        meta = self._find_meta(conversation_id)
        if not meta:
            return False

        # Remove the file
        conv_path = self.conversations_dir / f"{conversation_id}.json"
        if conv_path.exists():
            conv_path.unlink()

        # Remove from index
        self._index = [m for m in self._index if m.id != conversation_id]

        # If we deleted the active conversation, switch to most recent (or create new)
        if self._active_id == conversation_id:
            if self._index:
                self.switch(self._index[0].id)
            else:
                self.create_new()

        self._save_index()
        return True

    def update_title(self, conversation_id: str, title: str) -> None:
        """Update the title of a conversation."""
        meta = self._find_meta(conversation_id)
        if meta:
            meta.title = title[:TITLE_MAX_LENGTH]
            self._save_index()

    def auto_title_from_message(self, conversation_id: str, content: str) -> None:
        """Auto-set title from first user message if still default."""
        meta = self._find_meta(conversation_id)
        if not meta or meta.title != "New conversation":
            return
        title = content.strip().replace("\n", " ")
        if len(title) > TITLE_MAX_LENGTH:
            title = title[:TITLE_MAX_LENGTH - 1] + "\u2026"
        meta.title = title
        self._save_index()

    def _sync_active_meta(self) -> None:
        """Sync the active conversation's metadata with its actual state."""
        meta = self._find_meta(self._active_id)
        if meta and self._active:
            meta.message_count = len(self._active.messages)
            if self._active.messages:
                meta.last_message_at = self._active.messages[-1].timestamp
            self._save_index()

    def _find_meta(self, conversation_id: str) -> ConversationMeta | None:
        for m in self._index:
            if m.id == conversation_id:
                return m
        return None

    # -- Index persistence --------------------------------------------------

    @property
    def _index_path(self) -> Path:
        return self.conversations_dir / "index.json"

    def _load_index(self) -> None:
        if not self._index_path.exists():
            return
        try:
            data = json.loads(self._index_path.read_text(encoding="utf-8"))
            self._active_id = data.get("active", "")
            self._index = [
                ConversationMeta(
                    id=c["id"],
                    title=c.get("title", "Untitled"),
                    created_at=c.get("created_at", 0),
                    last_message_at=c.get("last_message_at", 0),
                    message_count=c.get("message_count", 0),
                )
                for c in data.get("conversations", [])
            ]
        except Exception:
            logger.warning("Failed to load conversation index for %s", self.agent_id)
            self._index = []

    def _save_index(self) -> None:
        data = {
            "active": self._active_id,
            "conversations": [m.to_dict() for m in self._index],
        }
        self._index_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # -- Legacy migration ---------------------------------------------------

    def _migrate_legacy(self) -> None:
        """Migrate from single-file storage to directory-based."""
        legacy_path = self.data_dir / "conversations" / f"{self.agent_id}.json"
        if not legacy_path.exists() or not legacy_path.is_file():
            return

        migrated_id = f"{self.agent_id}_migrated"
        dest = self.conversations_dir / f"{migrated_id}.json"
        if dest.exists():
            return  # Already migrated

        logger.info("Migrating legacy conversation for %s", self.agent_id)
        shutil.move(str(legacy_path), str(dest))

        # Build index from the migrated file
        now = time.time()
        msg_count = 0
        last_ts = now
        try:
            msgs = json.loads(dest.read_text(encoding="utf-8"))
            msg_count = len(msgs)
            if msgs:
                last_ts = msgs[-1].get("timestamp", now)
        except Exception:
            pass

        index_data = {
            "active": migrated_id,
            "conversations": [
                {
                    "id": migrated_id,
                    "title": "Previous conversation",
                    "created_at": msgs[0].get("timestamp", now) if msgs else now,
                    "last_message_at": last_ts,
                    "message_count": msg_count,
                }
            ],
        }
        self._index_path.write_text(json.dumps(index_data, indent=2), encoding="utf-8")

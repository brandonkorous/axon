"""Conversation archival — saves raw conversations to the vault's conversations tree.

Conversations are archived as markdown files under the conversations/ independent
root. They are NOT linked from second-brain.md and are not part of active recall.
The memory manager can reference them via wikilinks from memory entries.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from axon.vault.frontmatter import write_frontmatter

logger = logging.getLogger(__name__)


def archive_conversation(
    vault_path: str | Path,
    conversation_id: str,
    messages: list[dict[str, Any]],
    agent_id: str = "",
    title: str = "",
) -> str | None:
    """Archive a conversation to the vault's conversations/ tree.

    Args:
        vault_path: Path to the vault root.
        conversation_id: Unique ID for the conversation.
        messages: List of message dicts with role, content, timestamp.
        agent_id: Agent that owns this conversation.
        title: Optional title (derived from first message if empty).

    Returns:
        Relative path to the archived file, or None if nothing to archive.
    """
    if not messages:
        return None

    vault = Path(vault_path)
    conv_dir = vault / "conversations"
    conv_dir.mkdir(parents=True, exist_ok=True)

    # Derive title from first user message if not provided
    if not title:
        for msg in messages:
            if msg.get("role") == "user" and msg.get("content", "").strip():
                title = msg["content"].strip()[:60]
                break
        if not title:
            title = f"Conversation {conversation_id}"

    # Build filename from date + conversation ID slug
    first_ts = messages[0].get("timestamp", 0)
    if first_ts:
        date_str = datetime.fromtimestamp(first_ts).strftime("%Y-%m-%d")
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")

    slug = conversation_id[-12:] if len(conversation_id) > 12 else conversation_id
    filename = f"{date_str}-{slug}.md"
    filepath = conv_dir / filename

    # Build metadata
    metadata: dict[str, Any] = {
        "name": title,
        "description": f"Archived conversation: {title}",
        "type": "conversation",
        "memory_tier": "conversation",
        "conversation_id": conversation_id,
        "agent_id": agent_id,
        "message_count": len(messages),
        "date": date_str,
        "status": "archived",
    }

    # Build body — compact format, not full JSON
    body_parts = [f"# {title}\n"]
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        if not content.strip():
            continue
        # Skip tool results — they're noise in the archive
        if role == "tool":
            continue
        role_label = {"user": "User", "assistant": "Agent", "system": "System"}.get(role, role)
        body_parts.append(f"**{role_label}:** {content}\n")

    body = "\n".join(body_parts)

    # Write the archive file
    filepath.write_text(write_frontmatter(metadata, body), encoding="utf-8")

    # Update conversations index
    _update_conv_index(conv_dir, filename, title, date_str)

    rel_path = f"conversations/{filename}"
    logger.info("Archived conversation %s → %s", conversation_id, rel_path)
    return rel_path


def _update_conv_index(conv_dir: Path, filename: str, title: str, date_str: str) -> None:
    """Add a link to the conversation in the index file."""
    index_path = conv_dir / "conv-index.md"
    if not index_path.exists():
        return

    content = index_path.read_text(encoding="utf-8")
    stem = Path(filename).stem
    link = f"[[conversations/{stem}]]"
    if link in content:
        return

    content = content.rstrip() + f"\n- {date_str}: [[conversations/{stem}|{title}]]\n"
    index_path.write_text(content, encoding="utf-8")

"""Memory splitter — enforces character limits on memory fragments.

When a memory exceeds the configured character limit, splits it into smaller
linked fragments. Each fragment is a self-contained partial with wikilinks
to its siblings, enabling associative recall.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

MAX_BODY_CHARS = 200
# Split target is ~75% of max to leave room for linking text
SPLIT_TARGET_RATIO = 0.75


@dataclass
class MemoryFragment:
    """A single memory fragment ready for vault storage."""

    name: str
    body: str
    tags: str
    related_files: list[str]
    sibling_names: list[str]  # other fragments from the same split


def _truncate_at_word(text: str, max_chars: int) -> str:
    """Truncate text to max_chars, walking back to the last space."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    # Walk back to last space to avoid mid-word split
    last_space = truncated.rfind(" ")
    if last_space > 0:
        return truncated[:last_space]
    return truncated


def needs_splitting(text: str, max_chars: int = MAX_BODY_CHARS) -> bool:
    """Check if a memory text exceeds the character limit."""
    return len(text) > max_chars


def split_memory(
    text: str,
    name: str,
    tags: str = "",
    related_files: list[str] | None = None,
    max_chars: int = MAX_BODY_CHARS,
) -> list[MemoryFragment]:
    """Split an oversized memory into linked fragments.

    Each fragment stays under max_chars and includes wikilinks to siblings.
    If the text is already within limits, returns a single fragment.
    """
    if not needs_splitting(text, max_chars):
        return [MemoryFragment(
            name=name, body=text, tags=tags,
            related_files=related_files or [], sibling_names=[],
        )]

    target_chars = int(max_chars * SPLIT_TARGET_RATIO)
    chunks = _split_into_chunks(text, target_chars)

    if len(chunks) == 1:
        return [MemoryFragment(
            name=name, body=chunks[0], tags=tags,
            related_files=related_files or [], sibling_names=[],
        )]

    fragments: list[MemoryFragment] = []
    fragment_names = [f"{name} (part {i + 1})" for i in range(len(chunks))]

    for i, chunk in enumerate(chunks):
        siblings = [n for j, n in enumerate(fragment_names) if j != i]
        # Add sibling links at the end of the body
        links = "\n".join(f"- [[{_name_to_slug(s)}]]" for s in siblings)
        body = f"{chunk}\n\n**Related parts:**\n{links}"

        fragments.append(MemoryFragment(
            name=fragment_names[i],
            body=body,
            tags=tags,
            related_files=related_files or [],
            sibling_names=siblings,
        ))

    logger.debug("Split '%s' into %d fragments", name, len(fragments))
    return fragments


def _split_into_chunks(text: str, target_chars: int) -> list[str]:
    """Split text into chunks of roughly target_chars size.

    Prefers splitting at sentence boundaries, then word boundaries.
    """
    text = text.strip()

    # Try sentence-level splitting first
    sentences = re.split(r"(?<=[.!?])\s+", text)
    if len(sentences) >= 2:
        return _group_segments(sentences, target_chars, " ")

    # Fall back to word-boundary splitting
    return _force_split(text, target_chars)


def _group_segments(
    segments: list[str], target_chars: int, joiner: str,
) -> list[str]:
    """Group segments (sentences) into chunks close to target_chars."""
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for segment in segments:
        seg_len = len(segment)
        join_cost = len(joiner) if current else 0
        if current_len + join_cost + seg_len > target_chars and current:
            chunks.append(joiner.join(current))
            current = [segment]
            current_len = seg_len
        else:
            current.append(segment)
            current_len += join_cost + seg_len

    if current:
        chunks.append(joiner.join(current))

    return chunks


def _force_split(text: str, target_chars: int) -> list[str]:
    """Force-split text at word boundaries when no sentence breaks exist."""
    chunks: list[str] = []
    remaining = text

    while remaining:
        if len(remaining) <= target_chars:
            chunks.append(remaining)
            break
        chunk = _truncate_at_word(remaining, target_chars)
        chunks.append(chunk)
        remaining = remaining[len(chunk):].lstrip()

    return chunks


def _name_to_slug(name: str) -> str:
    """Convert a memory name to a vault-friendly slug."""
    slug = name.lower().replace(" ", "-")
    return "".join(c for c in slug if c.isalnum() or c == "-")

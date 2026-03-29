"""Memory splitter — enforces word limits on memory fragments.

When a memory exceeds the configured word limit, splits it into smaller
linked fragments. Each fragment is a self-contained partial with wikilinks
to its siblings, enabling associative recall.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_MAX_WORDS = 150
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


def count_words(text: str) -> int:
    """Count words in text, ignoring frontmatter and wikilinks."""
    clean = re.sub(r"\[\[.*?\]\]", "", text)
    return len(clean.split())


def needs_splitting(text: str, max_words: int = DEFAULT_MAX_WORDS) -> bool:
    """Check if a memory text exceeds the word limit."""
    return count_words(text) > max_words


def split_memory(
    text: str,
    name: str,
    tags: str = "",
    related_files: list[str] | None = None,
    max_words: int = DEFAULT_MAX_WORDS,
) -> list[MemoryFragment]:
    """Split an oversized memory into linked fragments.

    Each fragment stays under max_words and includes wikilinks to siblings.
    If the text is already within limits, returns a single fragment.
    """
    if not needs_splitting(text, max_words):
        return [MemoryFragment(
            name=name, body=text, tags=tags,
            related_files=related_files or [], sibling_names=[],
        )]

    target_words = int(max_words * SPLIT_TARGET_RATIO)
    chunks = _split_into_chunks(text, target_words)

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


def _split_into_chunks(text: str, target_words: int) -> list[str]:
    """Split text into chunks of roughly target_words size.

    Prefers splitting at paragraph boundaries, then sentence boundaries.
    """
    paragraphs = re.split(r"\n\s*\n", text.strip())

    if len(paragraphs) >= 2:
        return _group_paragraphs(paragraphs, target_words)

    # Single paragraph — split by sentences
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    if len(sentences) >= 2:
        return _group_sentences(sentences, target_words)

    # Can't split cleanly — force split by words
    return _force_split(text, target_words)


def _group_paragraphs(paragraphs: list[str], target_words: int) -> list[str]:
    """Group paragraphs into chunks close to target_words."""
    chunks: list[str] = []
    current: list[str] = []
    current_words = 0

    for para in paragraphs:
        para_words = len(para.split())
        if current_words + para_words > target_words and current:
            chunks.append("\n\n".join(current))
            current = [para]
            current_words = para_words
        else:
            current.append(para)
            current_words += para_words

    if current:
        chunks.append("\n\n".join(current))

    return chunks


def _group_sentences(sentences: list[str], target_words: int) -> list[str]:
    """Group sentences into chunks close to target_words."""
    chunks: list[str] = []
    current: list[str] = []
    current_words = 0

    for sentence in sentences:
        sent_words = len(sentence.split())
        if current_words + sent_words > target_words and current:
            chunks.append(" ".join(current))
            current = [sentence]
            current_words = sent_words
        else:
            current.append(sentence)
            current_words += sent_words

    if current:
        chunks.append(" ".join(current))

    return chunks


def _force_split(text: str, target_words: int) -> list[str]:
    """Force-split text by word count when no natural boundaries exist."""
    words = text.split()
    chunks: list[str] = []

    for i in range(0, len(words), target_words):
        chunks.append(" ".join(words[i:i + target_words]))

    return chunks


def _name_to_slug(name: str) -> str:
    """Convert a memory name to a vault-friendly slug."""
    slug = name.lower().replace(" ", "-")
    return "".join(c for c in slug if c.isalnum() or c == "-")

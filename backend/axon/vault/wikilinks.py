"""Wikilink parser and resolver for Obsidian-compatible markdown files."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


# Matches [[target]] and [[target|display text]]
WIKILINK_PATTERN = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")


@dataclass
class WikiLink:
    """A parsed wikilink with its target and surrounding context."""

    target: str  # The link target (e.g., "decisions/2026-03-20-pricing")
    display: str | None  # Optional display text after |
    context: str  # Surrounding text (for semantic signal)
    line_number: int


def extract_wikilinks(content: str, context_chars: int = 100) -> list[WikiLink]:
    """Extract all [[wikilinks]] from content with surrounding context.

    Args:
        content: The markdown content to search.
        context_chars: Number of characters of context to capture around each link.

    Returns:
        List of WikiLink objects with target, display text, and surrounding context.
    """
    links: list[WikiLink] = []
    lines = content.split("\n")

    for line_idx, line in enumerate(lines):
        for match in WIKILINK_PATTERN.finditer(line):
            target = match.group(1).strip()
            display = match.group(2)
            if display:
                display = display.strip()

            # Capture surrounding context from the full content
            start = max(0, match.start() - context_chars)
            end = min(len(line), match.end() + context_chars)
            context = line[start:end].strip()

            links.append(WikiLink(
                target=target,
                display=display,
                context=context,
                line_number=line_idx + 1,
            ))

    return links


def resolve_wikilink(
    target: str,
    vault_root: Path,
    current_file: Path | None = None,
    filename_index: dict[str, list[Path]] | None = None,
) -> Path | None:
    """Resolve a wikilink target to an actual file path.

    Resolution order:
    1. Exact path relative to vault root (with .md extension)
    2. Exact path relative to current file's directory
    3. Filename match anywhere in vault (Obsidian's shortest-path behavior)

    Args:
        filename_index: Optional pre-built mapping of filename -> [paths].
            When provided, avoids expensive rglob for step 3.

    Returns the resolved Path or None if not found.
    """
    # Normalize: strip .md if present, we'll add it back
    clean_target = target.removesuffix(".md")

    # 1. Exact path from vault root
    exact = vault_root / f"{clean_target}.md"
    if exact.exists():
        return exact

    # 2. Relative to current file's directory
    if current_file:
        relative = current_file.parent / f"{clean_target}.md"
        if relative.exists():
            return relative

    # 3. Filename match anywhere in vault
    filename = f"{clean_target.split('/')[-1]}.md"
    if filename_index is not None:
        matches = filename_index.get(filename)
        return matches[0] if matches else None

    # Fallback to rglob only when no index provided (single-file updates)
    for match in vault_root.rglob(filename):
        return match  # Return first match

    return None


def add_wikilink(content: str, target: str, section: str | None = None) -> str:
    """Add a [[wikilink]] to content.

    If section is provided, adds the link under that section header.
    Otherwise appends to the end.
    """
    link_text = f"[[{target}]]"

    if link_text in content:
        return content  # Already linked

    if section:
        # Find the section and add the link after it
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.strip().startswith("#") and section.lower() in line.lower():
                # Insert after section header and any existing content
                insert_idx = i + 1
                while insert_idx < len(lines) and lines[insert_idx].strip().startswith("- "):
                    insert_idx += 1
                lines.insert(insert_idx, f"- {link_text}")
                return "\n".join(lines)

    # Append to end
    return f"{content.rstrip()}\n- {link_text}\n"

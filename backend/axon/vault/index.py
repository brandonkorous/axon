"""Auto-update index files when vault files are written."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from axon.vault.frontmatter import parse_frontmatter


def ensure_index_entry(
    vault_root: Path,
    branch: str,
    file_name: str,
    description: str,
) -> None:
    """Ensure a file has an entry in its branch's index.

    Idempotent — won't add duplicates.
    """
    index_candidates = [
        vault_root / branch / f"{branch}-index.md",
        vault_root / branch / f"{branch}-log.md",
        vault_root / branch / f"{branch}.md",
    ]

    index_path = None
    for candidate in index_candidates:
        if candidate.exists():
            index_path = candidate
            break

    if index_path is None:
        return  # No index file to update

    content = index_path.read_text(encoding="utf-8")
    stem = file_name.removesuffix(".md")

    if f"[[{stem}]]" in content:
        return  # Already indexed

    entry = f"- [[{stem}]] — {description}"
    content = f"{content.rstrip()}\n{entry}\n"
    index_path.write_text(content, encoding="utf-8")

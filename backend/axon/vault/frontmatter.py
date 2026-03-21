"""YAML frontmatter parser/writer for Obsidian-compatible markdown files."""

from __future__ import annotations

from typing import Any

import frontmatter


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse a markdown file's YAML frontmatter and body.

    Returns (metadata_dict, body_string).
    """
    post = frontmatter.loads(content)
    return dict(post.metadata), post.content


def write_frontmatter(metadata: dict[str, Any], body: str) -> str:
    """Combine YAML frontmatter and body into a markdown string."""
    post = frontmatter.Post(body, **metadata)
    return frontmatter.dumps(post)


def read_file_with_frontmatter(path: str) -> tuple[dict[str, Any], str]:
    """Read a file and return (metadata, body)."""
    with open(path, encoding="utf-8") as f:
        content = f.read()
    return parse_frontmatter(content)


def write_file_with_frontmatter(path: str, metadata: dict[str, Any], body: str) -> None:
    """Write a file with YAML frontmatter."""
    content = write_frontmatter(metadata, body)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

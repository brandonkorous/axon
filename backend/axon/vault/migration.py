"""Vault migration — upgrades vault structure to current schema.

Runs on vault load. Detects old structure and migrates in place.
Each migration is idempotent — safe to run multiple times.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from axon.vault.frontmatter import parse_frontmatter, write_frontmatter

logger = logging.getLogger(__name__)


def migrate_vault(vault_path: str | Path) -> None:
    """Run all vault migrations. Safe to call on every load."""
    vault = Path(vault_path)
    if not vault.exists():
        return

    _migrate_learnings_to_memory_tiers(vault)
    _ensure_independent_roots(vault)


def _migrate_learnings_to_memory_tiers(vault: Path) -> None:
    """Migrate learnings/ -> memory/long-term/.

    Old structure: learnings/learnings-index.md + learnings/*.md
    New structure: memory/long-term/lt-index.md + memory/long-term/*.md
    """
    learnings_dir = vault / "learnings"
    if not learnings_dir.exists():
        return

    lt_dir = vault / "memory" / "long-term"
    st_dir = vault / "memory" / "short-term"
    memory_dir = vault / "memory"

    # Create new structure
    lt_dir.mkdir(parents=True, exist_ok=True)
    st_dir.mkdir(parents=True, exist_ok=True)

    # Create index files if they don't exist
    _ensure_index(memory_dir / "memory-index.md", "Memory Index",
                  "Active memory — short-term working context and long-term validated knowledge")
    _ensure_index(lt_dir / "lt-index.md", "Long-Term Memory",
                  "Validated insights and persistent knowledge with confidence tracking")
    _ensure_index(st_dir / "st-index.md", "Short-Term Memory",
                  "Working context from recent conversations — auto-expires after TTL")

    # Move learning files to long-term
    moved = 0
    for md_file in learnings_dir.glob("*.md"):
        if md_file.name == "learnings-index.md":
            continue
        dest = lt_dir / md_file.name
        if dest.exists():
            continue

        # Update memory_tier in frontmatter
        try:
            content = md_file.read_text(encoding="utf-8")
            metadata, body = parse_frontmatter(content)
            metadata["memory_tier"] = "long_term"
            dest.write_text(write_frontmatter(metadata, body), encoding="utf-8")
            md_file.unlink()
            moved += 1
        except Exception as e:
            logger.warning("Failed to migrate %s: %s", md_file, e)
            # Fallback: just copy the file
            shutil.copy2(md_file, dest)
            md_file.unlink()
            moved += 1

    if moved:
        logger.info("Migrated %d learnings to memory/long-term/", moved)

    # Update root file to link memory instead of learnings
    _update_root_links(vault)

    # Clean up empty learnings directory
    remaining = list(learnings_dir.glob("*.md"))
    if not remaining or (len(remaining) == 1 and remaining[0].name == "learnings-index.md"):
        shutil.rmtree(learnings_dir, ignore_errors=True)
        logger.info("Removed empty learnings/ directory")


def _ensure_independent_roots(vault: Path) -> None:
    """Ensure deep.md and conversations.md exist as independent roots."""
    deep_root = vault / "deep.md"
    conv_root = vault / "conversations.md"

    if not deep_root.exists():
        deep_dir = vault / "deep"
        deep_dir.mkdir(parents=True, exist_ok=True)
        _ensure_index(deep_dir / "deep-index.md", "Deep Memory",
                      "Forgotten memories awaiting user review before permanent deletion")
        # Detect agent name from second-brain.md
        agent_name = _detect_agent_name(vault)
        deep_root.write_text(
            f"# Deep Memory — {agent_name}\n\n"
            "Independent root for forgotten memories. Not linked from active knowledge tree.\n\n"
            "- [[deep/deep-index]]\n",
            encoding="utf-8",
        )
        logger.info("Created deep memory root: %s", deep_root)

    if not conv_root.exists():
        conv_dir = vault / "conversations"
        conv_dir.mkdir(parents=True, exist_ok=True)
        _ensure_index(conv_dir / "conv-index.md", "Conversations Archive",
                      "Archived raw conversation logs — reference only, not in active recall")
        agent_name = _detect_agent_name(vault)
        conv_root.write_text(
            f"# Conversations — {agent_name}\n\n"
            "Independent root for archived conversation logs. Not linked from active knowledge tree.\n\n"
            "- [[conversations/conv-index]]\n",
            encoding="utf-8",
        )
        logger.info("Created conversations root: %s", conv_root)


def _update_root_links(vault: Path) -> None:
    """Update second-brain.md to link memory/ instead of learnings/."""
    root_file = vault / "second-brain.md"
    if not root_file.exists():
        return

    content = root_file.read_text(encoding="utf-8")
    if "[[memory/memory-index]]" in content:
        return  # Already migrated

    # Replace learnings link with memory link
    if "[[learnings/" in content:
        # Remove the old learnings section
        lines = content.split("\n")
        new_lines: list[str] = []
        skip_until_next_section = False

        for line in lines:
            if "### Learnings" in line:
                skip_until_next_section = True
                continue
            if skip_until_next_section:
                if line.startswith("###") or line.startswith("##"):
                    skip_until_next_section = False
                elif line.strip().startswith("- [[learnings/"):
                    continue
                elif line.strip() and not line.startswith("-"):
                    continue
                else:
                    continue
            if not skip_until_next_section:
                new_lines.append(line)

        content = "\n".join(new_lines)

    # Add memory section after the first ## Branches or ## heading
    if "## Memory" not in content:
        insert_point = content.find("## Branches")
        if insert_point == -1:
            insert_point = content.find("## ")
        if insert_point > 0:
            memory_section = (
                "## Memory\n\n"
                "Active memory — short-term working context and long-term validated knowledge.\n"
                "- [[memory/memory-index]]\n\n"
            )
            content = content[:insert_point] + memory_section + content[insert_point:]

    root_file.write_text(content, encoding="utf-8")
    logger.info("Updated root file to link memory/ instead of learnings/")


def _ensure_index(path: Path, name: str, description: str) -> None:
    """Create an index file if it doesn't exist."""
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    metadata = {"name": name, "description": description, "type": "index"}
    body = f"# {name}\n\n{description}\n"
    path.write_text(write_frontmatter(metadata, body), encoding="utf-8")


def _detect_agent_name(vault: Path) -> str:
    """Try to read agent name from second-brain.md heading."""
    root = vault / "second-brain.md"
    if not root.exists():
        return "Agent"
    try:
        content = root.read_text(encoding="utf-8")
        for line in content.split("\n"):
            if line.startswith("# "):
                # "# Raj — CTO Advisor" -> "Raj"
                title = line[2:].strip()
                if " — " in title:
                    return title.split(" — ")[0]
                if " - " in title:
                    return title.split(" - ")[0]
                return title
    except Exception:
        pass
    return "Agent"

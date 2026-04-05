"""Execution actions for deep memory consolidation.

Handles merging, archiving, and contradiction-flagging of vault entries
as directed by the LLM consolidation review.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from axon.logging import get_logger
from axon.vault.vault import VaultManager

logger = get_logger(__name__)


@dataclass
class ConsolidationReport:
    """Summary of a deep consolidation run."""

    entries_reviewed: int = 0
    auto_archived: int = 0
    llm_merged: int = 0
    llm_archived: int = 0
    contradictions_flagged: int = 0
    orphans_adopted: int = 0
    orphans_linked_root: int = 0
    orphans_archived: int = 0
    batches_processed: int = 0
    errors: list[str] = field(default_factory=list)


def execute_merges(
    vault: VaultManager,
    merges: list[dict[str, Any]],
    today: str,
    report: ConsolidationReport,
) -> None:
    """Create merged entries and archive their sources."""
    for merge in merges:
        source_paths = merge.get("source_paths", [])
        insight = merge.get("merged_insight", "")
        if len(source_paths) < 2 or not insight:
            continue
        try:
            _create_merged_entry(vault, merge, source_paths, insight, today, report)
        except Exception as e:
            report.errors.append(f"Merge failed: {e}")


def execute_archives(
    vault: VaultManager,
    archives: list[dict[str, Any]],
    today: str,
    report: ConsolidationReport,
) -> None:
    """Archive entries flagged by the LLM."""
    for archive in archives:
        path = archive.get("path", "")
        reason = archive.get("reason", "flagged by consolidation review")
        if not path:
            continue
        try:
            metadata, body = vault.read_file(path)
            metadata["status"] = "archived"
            history = metadata.get("confidence_history", [])
            history.append({
                "date": today,
                "value": metadata.get("confidence", 0.5),
                "reason": f"archived — {reason}",
            })
            metadata["confidence_history"] = history
            vault.write_file(path, metadata, body)
            report.llm_archived += 1
        except Exception as e:
            report.errors.append(f"Archive failed for {path}: {e}")


def execute_contradictions(
    vault: VaultManager,
    contradictions: list[dict[str, Any]],
    today: str,
    report: ConsolidationReport,
) -> None:
    """Cross-link and lower confidence on contradictory entries."""
    for contradiction in contradictions:
        path_a = contradiction.get("path_a", "")
        path_b = contradiction.get("path_b", "")
        description = contradiction.get("description", "")
        if not path_a or not path_b:
            continue
        try:
            for src, tgt in [(path_a, path_b), (path_b, path_a)]:
                metadata, body = vault.read_file(src)
                ref = f"[[{Path(tgt).stem}]]"

                contradicted_by = metadata.get("contradicted_by", [])
                if ref not in contradicted_by:
                    contradicted_by.append(ref)
                metadata["contradicted_by"] = contradicted_by

                conf = float(metadata.get("confidence", 0.5))
                new_conf = max(0.0, round(conf - 0.1, 2))
                metadata["confidence"] = new_conf

                history = metadata.get("confidence_history", [])
                history.append({
                    "date": today,
                    "value": new_conf,
                    "reason": f"contradiction flagged: {description[:100]}",
                })
                metadata["confidence_history"] = history
                vault.write_file(src, metadata, body)

            report.contradictions_flagged += 1
        except Exception as e:
            report.errors.append(f"Contradiction failed for {path_a} vs {path_b}: {e}")


def execute_orphan_adoptions(
    vault: VaultManager,
    adoptions: list[dict[str, Any]],
    today: str,
    report: ConsolidationReport,
) -> None:
    """Link orphan files into the tree based on LLM recommendations."""
    for adoption in adoptions:
        path = adoption.get("path", "")
        action = adoption.get("action", "")
        if not path or not action:
            continue
        try:
            if action == "adopt":
                _adopt_into_branch(vault, adoption, report)
            elif action == "link_root":
                _link_to_root(vault, adoption, report)
            elif action == "archive":
                _archive_orphan(vault, path, adoption.get("reason", ""), today, report)
        except Exception as e:
            report.errors.append(f"Orphan adoption failed for {path}: {e}")


def _adopt_into_branch(
    vault: VaultManager,
    adoption: dict[str, Any],
    report: ConsolidationReport,
) -> None:
    """Link an orphan file into a branch index."""
    path = adoption["path"]
    branch = adoption.get("target_branch", "")
    if not branch:
        return

    name = Path(path).stem
    try:
        metadata, _ = vault.read_file(path)
    except FileNotFoundError:
        return
    description = metadata.get("description", metadata.get("name", name))
    vault._update_branch_index(branch, name, description)
    report.orphans_adopted += 1


def _link_to_root(
    vault: VaultManager,
    adoption: dict[str, Any],
    report: ConsolidationReport,
) -> None:
    """Link an orphan file directly from the root."""
    path = adoption["path"]
    stem = Path(path).stem
    root = vault.vault_path / vault.root_file
    if not root.exists():
        return

    content = root.read_text(encoding="utf-8")
    if f"[[{stem}]]" in content or f"[[{path.removesuffix('.md')}]]" in content:
        return  # Already linked

    content = content.rstrip() + f"\n- [[{stem}]]\n"
    root.write_text(content, encoding="utf-8")
    vault.cache.update(vault.root_file)
    vault._invalidate_graph()
    report.orphans_linked_root += 1


def _archive_orphan(
    vault: VaultManager,
    path: str,
    reason: str,
    today: str,
    report: ConsolidationReport,
) -> None:
    """Mark an orphan as archived."""
    try:
        metadata, body = vault.read_file(path)
    except FileNotFoundError:
        return
    metadata["status"] = "archived"
    history = metadata.get("confidence_history", [])
    history.append({
        "date": today,
        "value": metadata.get("confidence", 0.0),
        "reason": f"orphan archived — {reason}",
    })
    metadata["confidence_history"] = history
    vault.write_file(path, metadata, body, auto_link=False)
    report.orphans_archived += 1


# ── Internal helpers ─────────────────────────────────────────────


def _create_merged_entry(
    vault: VaultManager,
    merge: dict[str, Any],
    source_paths: list[str],
    insight: str,
    today: str,
    report: ConsolidationReport,
) -> None:
    """Create a single merged entry and archive its sources."""
    total_convos = 0
    all_tags: set[str] = set()
    source_refs: list[str] = []

    for sp in source_paths:
        try:
            meta, _ = vault.read_file(sp)
            total_convos += int(meta.get("source_conversations", 1))
            for tag in str(meta.get("tags", "")).split(","):
                tag = tag.strip()
                if tag:
                    all_tags.add(tag)
            source_refs.append(f"[[{Path(sp).stem}]]")
        except Exception:
            continue

    tags = merge.get("tags", ", ".join(sorted(all_tags)))
    confidence = min(0.9, merge.get("merged_confidence", 0.7))

    slug = insight[:50].lower().replace(" ", "-")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    filename = f"{today}-{slug}"

    metadata: dict[str, Any] = {
        "name": insight[:100],
        "description": insight[:200],
        "type": "learning",
        "learning_type": "consolidated",
        "confidence": round(confidence, 2),
        "confidence_history": [{
            "date": today,
            "value": round(confidence, 2),
            "reason": f"consolidated from {len(source_paths)} entries",
        }],
        "validated_by": [],
        "contradicted_by": [],
        "last_validated": today,
        "source_conversations": total_convos,
        "tags": tags,
        "status": "active",
        "date": today,
    }

    body = f"## Insight\n{insight}\n\n## Evidence\n"
    for ref in source_refs:
        body += f"- {ref}\n"

    vault.create_file("learnings", filename, metadata, body)

    # Archive sources
    new_ref = f"[[{slug}]]"
    for sp in source_paths:
        try:
            meta, src_body = vault.read_file(sp)
            meta["status"] = "archived"
            history = meta.get("confidence_history", [])
            history.append({
                "date": today,
                "value": meta.get("confidence", 0.5),
                "reason": f"merged into {new_ref}",
            })
            meta["confidence_history"] = history
            vault.write_file(sp, meta, src_body)
        except Exception:
            continue

    report.llm_merged += 1

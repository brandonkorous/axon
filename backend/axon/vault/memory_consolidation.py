"""Deep memory consolidation — LLM-driven periodic vault review.

Merges redundant entries, surfaces higher-level patterns, archives dead
weight, and flags contradictions. Runs on the cheap local model.
"""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING, Any

from axon.agents.provider import complete
from axon.config import LearningConfig
from axon.vault.memory_consolidation_actions import (
    ConsolidationReport,
    execute_archives,
    execute_contradictions,
    execute_merges,
)
from axon.vault.memory_prompts import CONSOLIDATION_REVIEW_PROMPT, parse_llm_json
from axon.vault.vault import VaultManager

if TYPE_CHECKING:
    from axon.usage import UsageTracker

logger = logging.getLogger(__name__)
__all__ = ["deep_consolidate", "ConsolidationReport"]


async def deep_consolidate(
    vault: VaultManager,
    config: LearningConfig,
    model: str,
    usage_tracker: "UsageTracker | None" = None,
    agent_id: str = "",
    org_id: str = "",
) -> ConsolidationReport:
    """Run LLM-driven deep consolidation on the vault's learnings."""
    report = ConsolidationReport()
    today = str(date.today())

    # Phase 1: Load active entries
    entries = _load_active_entries(vault)
    report.entries_reviewed = len(entries)

    if len(entries) < config.deep_consolidation_min_entries:
        logger.debug("[%s] Deep consolidation skipped — %d entries", agent_id, len(entries))
        return report

    # Phase 2: Auto-archive low-confidence entries (no LLM needed)
    remaining = _auto_archive(vault, config, entries, today)
    report.auto_archived = len(entries) - len(remaining)
    if len(remaining) < config.deep_consolidation_min_entries:
        return report

    # Phase 3+4: Batch, send to LLM, execute actions
    batches = _make_batches(remaining, config.deep_consolidation_batch_size)
    for batch in batches:
        report.batches_processed += 1
        try:
            actions = await _review_batch(batch, model, config, usage_tracker, agent_id, org_id)
            if not actions:
                continue
            execute_merges(vault, actions.get("merges", []), today, report)
            execute_archives(vault, actions.get("archives", []), today, report)
            execute_contradictions(vault, actions.get("contradictions", []), today, report)
        except Exception as e:
            error_msg = f"Batch {report.batches_processed} failed: {e}"
            logger.warning("[%s] %s", agent_id, error_msg)
            report.errors.append(error_msg)

    logger.info(
        "[%s] Deep consolidation complete — reviewed=%d, auto_archived=%d, "
        "merged=%d, archived=%d, contradictions=%d, errors=%d",
        agent_id, report.entries_reviewed, report.auto_archived,
        report.llm_merged, report.llm_archived,
        report.contradictions_flagged, len(report.errors),
    )
    return report


def _load_active_entries(
    vault: VaultManager,
) -> list[tuple[str, dict[str, Any], str]]:
    """Load all active learnings as (path, metadata, body) tuples."""
    entries: list[tuple[str, dict[str, Any], str]] = []
    for item in vault.list_branch("learnings"):
        path = item.get("path", "")
        if not path:
            continue
        try:
            metadata, body = vault.read_file(path)
            if metadata.get("status", "active") == "active":
                entries.append((path, metadata, body))
        except Exception:
            continue
    return entries


def _auto_archive(
    vault: VaultManager,
    config: LearningConfig,
    entries: list[tuple[str, dict[str, Any], str]],
    today: str,
) -> list[tuple[str, dict[str, Any], str]]:
    """Archive entries below confidence threshold without LLM review."""
    remaining: list[tuple[str, dict[str, Any], str]] = []
    today_date = date.fromisoformat(today)

    for path, metadata, body in entries:
        confidence = float(metadata.get("confidence", 0.5))
        validated_by = metadata.get("validated_by", [])
        last_validated = metadata.get("last_validated", "")

        should_archive = (
            confidence < config.archive_confidence_threshold
            and not validated_by
            and last_validated
            and (today_date - date.fromisoformat(last_validated)).days > config.confidence_decay_days
        )

        if should_archive:
            metadata["status"] = "archived"
            history = metadata.get("confidence_history", [])
            history.append({
                "date": today,
                "value": confidence,
                "reason": "auto-archived — below confidence threshold",
            })
            metadata["confidence_history"] = history
            vault.write_file(path, metadata, body)
        else:
            remaining.append((path, metadata, body))

    return remaining


def _make_batches(
    entries: list[tuple[str, dict[str, Any], str]], batch_size: int,
) -> list[list[tuple[str, dict[str, Any], str]]]:
    return [entries[i:i + batch_size] for i in range(0, len(entries), batch_size)]


def _build_batch_summary(batch: list[tuple[str, dict[str, Any], str]]) -> str:
    """Format a batch of entries for the consolidation prompt."""
    today = date.today()
    lines: list[str] = []
    for path, metadata, body in batch:
        name = metadata.get("name", Path(path).stem)
        confidence = metadata.get("confidence", 0.5)
        tags = metadata.get("tags", "")
        created = metadata.get("date", "")
        age_days = (today - date.fromisoformat(created)).days if created else 0
        insight_text = body.replace("## Insight\n", "").split("\n## ")[0].strip()
        excerpt = insight_text[:150]
        lines.append(f"[{path}] {name} (confidence={confidence}, age={age_days}d, tags={tags})")
        lines.append(f"> {excerpt}")
        lines.append("")
    return "\n".join(lines)


async def _review_batch(
    batch: list[tuple[str, dict[str, Any], str]],
    model: str,
    config: LearningConfig,
    usage_tracker: "UsageTracker | None",
    agent_id: str,
    org_id: str,
) -> dict[str, Any] | None:
    """Send a batch to the local LLM for consolidation review."""
    summary = _build_batch_summary(batch)
    prompt = CONSOLIDATION_REVIEW_PROMPT.format(entries=summary)

    response = await complete(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=config.memory_max_tokens,
        temperature=0.1,
    )

    if usage_tracker:
        usage = response.get("usage")
        if usage:
            try:
                usage_tracker.record(
                    model=model,
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    total_tokens=usage.get("total_tokens", 0),
                    cost=usage.get("cost", 0.0),
                    agent_id=agent_id, org_id=org_id,
                    call_type="completion", caller="memory_consolidation",
                )
            except Exception:
                pass

    return parse_llm_json(response.get("content", ""))

"""Memory learning — outbound side of the MemoryManager.

Extracts learnings from conversation turns, updates confidence on existing
vault entries, handles outcome linking and confidence decay.
"""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING, Any

from axon.agents.provider import complete
from axon.config import LearningConfig

if TYPE_CHECKING:
    from axon.usage import UsageTracker
from axon.vault.memory_prompts import PROCESS_TURN_PROMPT, parse_llm_json
from axon.vault.vault import VaultManager

logger = logging.getLogger(__name__)


async def extract_learnings(
    vault: VaultManager,
    config: LearningConfig,
    model: str,
    user_message: str,
    assistant_response: str,
    vault_context: str,
    usage_tracker: "UsageTracker | None" = None,
    agent_id: str = "",
    org_id: str = "",
) -> None:
    """Use the local LLM to extract learnings from a conversation turn."""
    logger.debug("LEARN — asking local model to analyze turn (model=%s)", model)
    prompt = PROCESS_TURN_PROMPT.format(
        user_message=user_message,
        assistant_response=assistant_response[:2000],
        vault_context=vault_context[:1000] if vault_context else "None",
    )
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
                    call_type="completion", caller="memory_learning",
                )
            except Exception:
                pass
    result = parse_llm_json(response.get("content", ""))
    logger.debug("LEARN — local model result: %s", result)
    if not result or not result.get("worth_saving"):
        logger.debug("LEARN — nothing worth saving this turn")
        return

    today = str(date.today())
    insights = result.get("insights", [])
    updates = result.get("confidence_updates", [])
    contradictions = result.get("contradictions", [])
    logger.debug(
        "LEARN — saving: %d insights, %d confidence updates, %d contradictions",
        len(insights), len(updates), len(contradictions),
    )
    _write_insights(vault, insights, today)
    _apply_confidence_updates(vault, updates, today)
    _apply_contradictions(vault, contradictions, today)
    logger.debug("LEARN — all writes complete")


async def link_outcome(
    vault: VaultManager,
    outcome_path: str,
    related_paths: list[str],
    outcome_type: str,
) -> str:
    """Link a known outcome to prior decisions and update confidence."""
    adjustments = {"positive": 0.15, "negative": -0.2, "mixed": 0.05}
    delta = adjustments.get(outcome_type, 0.0)
    updated: list[str] = []

    for path in related_paths:
        try:
            metadata, body = vault.read_file(path)
            confidence = float(metadata.get("confidence", 0.5))
            new_conf = max(0.0, min(0.95, confidence + delta))

            metadata["confidence"] = round(new_conf, 2)
            metadata["last_validated"] = str(date.today())

            history = metadata.get("confidence_history", [])
            history.append({
                "date": str(date.today()),
                "value": round(new_conf, 2),
                "reason": f"{outcome_type} outcome from [[{Path(outcome_path).stem}]]",
            })
            metadata["confidence_history"] = history

            link_ref = f"[[{Path(outcome_path).stem}]]"
            if outcome_type == "positive":
                validated = metadata.get("validated_by", [])
                if link_ref not in validated:
                    validated.append(link_ref)
                metadata["validated_by"] = validated
            elif outcome_type == "negative":
                contradicted = metadata.get("contradicted_by", [])
                if link_ref not in contradicted:
                    contradicted.append(link_ref)
                metadata["contradicted_by"] = contradicted

            vault.write_file(path, metadata, body)
            updated.append(f"{path}: {confidence:.2f} → {new_conf:.2f}")
        except Exception as e:
            logger.warning("Failed to update %s: %s", path, e)

    if updated:
        return f"Updated {len(updated)} files: " + "; ".join(updated)
    return "No files updated."


def apply_confidence_decay(
    vault: VaultManager,
    config: LearningConfig,
    learnings: list[dict[str, Any]],
) -> None:
    """Decay confidence on old unvalidated entries."""
    today = date.today()
    for entry in learnings:
        path = entry.get("path", "")
        if not path:
            continue
        try:
            metadata, body = vault.read_file(path)
            last_validated = metadata.get("last_validated", "")
            if not last_validated:
                continue

            validated_date = date.fromisoformat(last_validated)
            days_since = (today - validated_date).days
            if days_since <= config.confidence_decay_days:
                continue
            if metadata.get("validated_by"):
                continue

            conf = float(metadata.get("confidence", 0.5))
            new_conf = max(0.0, conf - 0.1)
            if new_conf == conf:
                continue

            metadata["confidence"] = round(new_conf, 2)
            history = metadata.get("confidence_history", [])
            history.append({
                "date": str(today),
                "value": round(new_conf, 2),
                "reason": f"decay — {days_since} days without validation",
            })
            metadata["confidence_history"] = history
            vault.write_file(path, metadata, body)
        except Exception as e:
            logger.warning("Confidence decay failed for %s: %s", path, e)


# ── Internal helpers ─────────────────────────────────────────────


def _ensure_learnings_linked(vault: VaultManager) -> None:
    """Ensure the vault's root file links to the learnings branch.

    If the root file exists but doesn't contain a [[learnings/ link,
    append a Learnings section. This prevents orphaned subtrees.
    """
    root_path = Path(vault.vault_path) / vault.root_file
    if not root_path.exists():
        return

    content = root_path.read_text(encoding="utf-8")
    if "[[learnings/" in content:
        return  # Already linked

    # Append the learnings branch link
    content = content.rstrip() + (
        "\n\n### Learnings\n"
        "Auto-extracted insights, patterns, and corrections from conversations.\n"
        "- [[learnings/learnings-index|Learnings]]\n"
    )
    root_path.write_text(content, encoding="utf-8")
    logger.info("LEARN — linked learnings branch to root file: %s", vault.root_file)


def _write_insights(
    vault: VaultManager, insights: list[dict[str, Any]], today: str,
) -> None:
    """Write new insight files to the learnings/ branch."""
    if insights:
        _ensure_learnings_linked(vault)

    for insight_data in insights:
        insight = insight_data.get("insight", "")
        if not insight:
            continue

        slug = insight[:50].lower().replace(" ", "-")
        slug = "".join(c for c in slug if c.isalnum() or c == "-")
        filename = f"{today}-{slug}"
        logger.debug("LEARN — writing insight: %s → learnings/%s", insight[:80], filename)

        metadata: dict[str, Any] = {
            "name": insight[:100],
            "description": insight[:200],
            "type": "learning",
            "learning_type": "insight",
            "confidence": insight_data.get("confidence", 0.6),
            "confidence_history": [{
                "date": today,
                "value": insight_data.get("confidence", 0.6),
                "reason": "extracted from conversation",
            }],
            "validated_by": [],
            "contradicted_by": [],
            "last_validated": today,
            "source_conversations": 1,
            "tags": insight_data.get("tags", ""),
            "status": "active",
            "date": today,
        }

        body = f"## Insight\n{insight}\n"
        related = insight_data.get("related_files", [])
        if related:
            body += "\n## Evidence\n"
            for ref in related:
                body += f"- [[{Path(ref).stem}]]\n"

        vault.create_file("learnings", filename, metadata, body)


def _apply_confidence_updates(
    vault: VaultManager, updates: list[dict[str, Any]], today: str,
) -> None:
    """Update confidence on existing vault files."""
    for update in updates:
        path = update.get("path", "")
        if not path:
            continue
        try:
            metadata, body = vault.read_file(path)
            new_conf = max(0.0, min(0.95, update.get("new_confidence", 0.5)))
            metadata["confidence"] = round(new_conf, 2)
            metadata["last_validated"] = today

            convos = int(metadata.get("source_conversations", 0))
            metadata["source_conversations"] = convos + 1

            history = metadata.get("confidence_history", [])
            history.append({
                "date": today,
                "value": round(new_conf, 2),
                "reason": update.get("reason", "updated by memory manager"),
            })
            metadata["confidence_history"] = history
            vault.write_file(path, metadata, body)
        except Exception as e:
            logger.warning("Failed to update confidence for %s: %s", path, e)


def _apply_contradictions(
    vault: VaultManager, contradictions: list[dict[str, Any]], today: str,
) -> None:
    """Lower confidence on contradicted vault entries."""
    for contradiction in contradictions:
        path = contradiction.get("path", "")
        if not path:
            continue
        try:
            metadata, body = vault.read_file(path)
            conf = float(metadata.get("confidence", 0.5))
            new_conf = max(0.0, conf - 0.2)
            metadata["confidence"] = round(new_conf, 2)

            history = metadata.get("confidence_history", [])
            history.append({
                "date": today,
                "value": round(new_conf, 2),
                "reason": f"contradicted: {contradiction.get('contradiction', '')}",
            })
            metadata["confidence_history"] = history
            vault.write_file(path, metadata, body)
        except Exception as e:
            logger.warning("Failed to process contradiction for %s: %s", path, e)

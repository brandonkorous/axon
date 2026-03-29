"""Memory recall — inbound side of the MemoryManager.

Uses a local LLM to semantically search the vault and curate context
for the paid reasoning model. Falls back to deterministic search.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from axon.agents.provider import complete
from axon.config import LearningConfig

if TYPE_CHECKING:
    from axon.usage import UsageTracker
from axon.vault.memory_prompts import RECALL_PLAN_PROMPT, RECALL_RANK_PROMPT, parse_llm_json
from axon.vault.vault import VaultManager

logger = logging.getLogger(__name__)


async def recall_with_llm(
    vault: VaultManager,
    config: LearningConfig,
    model: str,
    user_message: str,
    usage_tracker: "UsageTracker | None" = None,
    agent_id: str = "",
    org_id: str = "",
) -> str:
    """Use the local LLM to semantically search and curate vault context."""
    vault_summary = _build_vault_summary(vault)
    logger.debug("RECALL step 1/4 — planning search (model=%s)", model)
    logger.debug("RECALL vault summary:\n%s", vault_summary)

    # Step 1: Ask the local model what to search for
    plan_prompt = RECALL_PLAN_PROMPT.format(
        vault_summary=vault_summary, user_message=user_message,
    )
    plan_response = await complete(
        model=model,
        messages=[{"role": "user", "content": plan_prompt}],
        max_tokens=config.memory_max_tokens,
        temperature=0.1,
    )
    _record_usage(usage_tracker, model, plan_response, agent_id, org_id, "memory_recall")
    plan = parse_llm_json(plan_response.get("content", ""))
    logger.debug("RECALL step 1/4 — plan result: %s", plan)
    if not plan or not plan.get("needs_context"):
        logger.debug("RECALL — local model says no context needed, returning empty")
        return ""

    # Step 2: Execute searches
    queries = plan.get("search_queries", [])
    branches = plan.get("branches", [])
    logger.debug("RECALL step 2/4 — searching vault: queries=%s, branches=%s", queries, branches)
    candidates = _execute_searches(vault, queries, branches)
    logger.debug("RECALL step 2/4 — found %d candidate files", len(candidates))
    if not candidates:
        logger.debug("RECALL — no candidates found, returning empty")
        return ""

    # Step 3: Ask the local model to rank candidates
    candidates_text = _format_candidates(vault, candidates)
    logger.debug("RECALL step 3/4 — ranking %d candidates", len(candidates))
    rank_prompt = RECALL_RANK_PROMPT.format(
        user_message=user_message, candidates=candidates_text,
    )
    rank_response = await complete(
        model=model,
        messages=[{"role": "user", "content": rank_prompt}],
        max_tokens=config.memory_max_tokens,
        temperature=0.1,
    )
    _record_usage(usage_tracker, model, rank_response, agent_id, org_id, "memory_recall")
    ranking = parse_llm_json(rank_response.get("content", ""))
    ranked_paths = ranking.get("ranked_paths", []) if ranking else []
    logger.debug("RECALL step 3/4 — ranked paths: %s", ranked_paths)

    # Step 4: Build context from ranked paths within token budget
    result = _build_context(vault, config, ranked_paths, candidates)
    logger.debug("RECALL step 4/4 — built context: %d chars", len(result))
    return result


def recall_fallback(
    vault: VaultManager, config: LearningConfig, user_message: str,
) -> str:
    """Deterministic fallback when the local LLM is unavailable."""
    logger.debug("RECALL FALLBACK — using deterministic MemoryNavigator")
    from axon.vault.navigator import MemoryNavigator

    nav = MemoryNavigator(vault.vault_path, vault.root_file, cache=vault.cache)
    result = nav._search_and_rank(user_message, config.max_recall_tokens)
    context = nav._format_context(result)
    logger.debug("RECALL FALLBACK — returned %d chars", len(context))
    return context


def _build_vault_summary(vault: VaultManager) -> str:
    """Build a compact summary of vault structure for the local model."""
    lines: list[str] = []
    for branch_dir in sorted(vault.vault_path.iterdir()):
        if not branch_dir.is_dir() or branch_dir.name.startswith("."):
            continue
        file_count = sum(1 for _ in branch_dir.glob("*.md"))
        lines.append(f"- {branch_dir.name}/ ({file_count} files)")

    hubs = vault.graph.get_most_connected(5)
    if hubs:
        lines.append("\nKey topics (most connected):")
        for node in hubs:
            lines.append(
                f"- {node.title} ({node.path}) "
                f"[{node.link_count} links, {node.backlink_count} backlinks]"
            )
    return "\n".join(lines) if lines else "Empty vault."


def _execute_searches(
    vault: VaultManager, queries: list[str], branches: list[str],
) -> dict[str, dict[str, Any]]:
    """Execute search queries against the vault, return candidate files.

    Prioritizes memory tiers: short-term first, then long-term, then other
    branches. Never searches deep/ or conversations/ — those are archived.
    """
    # Excluded paths — archived trees with independent roots
    excluded_prefixes = ("deep/", "conversations/")

    candidates: dict[str, dict[str, Any]] = {}

    # Priority 1: Search memory tiers directly
    for memory_branch in ["memory/short-term", "memory/long-term"]:
        for f in vault.list_branch(memory_branch)[:10]:
            if f["path"] not in candidates:
                candidates[f["path"]] = {
                    "path": f["path"],
                    "title": f.get("title", f["name"]),
                    "snippet": f.get("description", ""),
                }

    # Priority 2: Execute search queries
    for query in queries[:3]:
        for r in vault.search(query, max_results=5):
            path = r["path"]
            if any(path.startswith(p) for p in excluded_prefixes):
                continue
            if path not in candidates:
                candidates[path] = r

    # Priority 3: Browse requested branches (excluding archived)
    for branch in branches[:3]:
        if any(branch.startswith(p.rstrip("/")) for p in excluded_prefixes):
            continue
        for f in vault.list_branch(branch)[:5]:
            if f["path"] not in candidates:
                candidates[f["path"]] = {
                    "path": f["path"],
                    "title": f.get("title", f["name"]),
                    "snippet": f.get("description", ""),
                }
    return candidates


def _format_candidates(
    vault: VaultManager, candidates: dict[str, dict[str, Any]],
) -> str:
    """Format candidate files for the ranking prompt."""
    lines: list[str] = []
    for path, info in candidates.items():
        conf_str = ""
        try:
            metadata, _ = vault.read_file(path)
            conf = metadata.get("confidence")
            if conf is not None:
                conf_str = f" [confidence: {conf}]"
        except Exception:
            pass
        lines.append(f"- **{info.get('title', path)}** (`{path}`){conf_str}")
        snippet = info.get("snippet", "")
        if snippet:
            lines.append(f"  {snippet[:200]}")
    return "\n".join(lines)


def _build_context(
    vault: VaultManager,
    config: LearningConfig,
    ranked_paths: list[str],
    candidates: dict[str, dict[str, Any]],
) -> str:
    """Build formatted context from ranked paths within token budget."""
    sections: list[str] = []
    tokens_used = 0
    budget = config.max_recall_tokens

    for path in ranked_paths:
        if path not in candidates:
            continue
        try:
            content = vault.read_file_raw(path)
        except FileNotFoundError:
            continue

        estimated_tokens = len(content) // 4
        if tokens_used + estimated_tokens > budget:
            remaining = budget - tokens_used
            if remaining > 200:
                content = content[: remaining * 4]
                estimated_tokens = remaining
            else:
                continue

        title = candidates[path].get("title", Path(path).stem)
        sections.append(f"### {title} (`{path}`)\n{content}")
        tokens_used += estimated_tokens
        if tokens_used >= budget:
            break

    return "\n\n---\n\n".join(sections) if sections else ""


def _record_usage(
    tracker: "UsageTracker | None",
    model: str,
    response: dict[str, Any],
    agent_id: str,
    org_id: str,
    caller: str,
) -> None:
    """Record usage from a complete() response if tracker is available."""
    if not tracker:
        return
    usage = response.get("usage")
    if not usage:
        return
    try:
        tracker.record(
            model=model,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            cost=usage.get("cost", 0.0),
            agent_id=agent_id,
            org_id=org_id,
            call_type="completion",
            caller=caller,
        )
    except Exception:
        pass

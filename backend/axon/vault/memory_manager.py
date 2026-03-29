"""MemoryManager — local-LLM-powered memory for agent vaults.

Three-tier memory architecture:
- short-term: working context from recent conversations (5-7 day TTL)
- long-term: validated insights and persistent knowledge
- deep: forgotten memories awaiting user review before deletion

INBOUND:  recall() searches short-term then long-term before reasoning
OUTBOUND: process_turn() extracts memories after the paid model responds

Uses a cheap local model (e.g. ollama/llama3:8b) for all memory work.
Falls back to deterministic MemoryNavigator if the local model is unavailable.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
from datetime import date, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

from axon.config import LearningConfig
from axon.vault.frontmatter import parse_frontmatter, write_frontmatter
from axon.vault.memory_recall import recall_with_llm, recall_fallback
from axon.vault.memory_learning import extract_learnings, link_outcome, apply_confidence_decay
from axon.vault.vault import VaultManager

if TYPE_CHECKING:
    from axon.usage import UsageTracker

logger = logging.getLogger(__name__)


class MemoryManager:
    """Local-LLM-powered memory manager for agent vaults.

    Handles both recall (inbound) and learning (outbound) using a cheap
    local model. Falls back to deterministic search if the model is unavailable.
    """

    def __init__(
        self,
        vault: VaultManager,
        config: LearningConfig,
        model: str,
        agent_id: str = "",
        usage_tracker: "UsageTracker | None" = None,
        org_id: str = "",
    ):
        self.vault = vault
        self.config = config
        self.model = model
        self.agent_id = agent_id
        self._usage_tracker = usage_tracker
        self._org_id = org_id
        self._turn_count = 0

    async def recall(self, user_message: str) -> str:
        """Retrieve relevant vault context for a user message."""
        logger.debug(
            "[%s] 🔍 RECALL START — message: %.80s...",
            self.agent_id, user_message,
        )
        try:
            result = await recall_with_llm(
                self.vault, self.config, self.model, user_message,
                usage_tracker=self._usage_tracker,
                agent_id=self.agent_id, org_id=self._org_id,
            )
            logger.debug(
                "[%s] 🔍 RECALL COMPLETE — returned %d chars of context",
                self.agent_id, len(result),
            )
            return result
        except TimeoutError:
            logger.warning("[%s] MemoryManager recall timed out — using fallback", self.agent_id)
            return await asyncio.to_thread(recall_fallback, self.vault, self.config, user_message)
        except Exception as e:
            logger.warning("[%s] MemoryManager recall failed — using fallback: %s", self.agent_id, e)
            return await asyncio.to_thread(recall_fallback, self.vault, self.config, user_message)

    async def process_turn(
        self,
        user_message: str,
        assistant_response: str,
        vault_context: str,
        conversation_id: str = "",
    ) -> None:
        """Process a completed turn — extract and store memories."""
        self._turn_count += 1
        logger.debug(
            "[%s] 📝 LEARN START — turn #%d, response: %d chars, context: %d chars",
            self.agent_id, self._turn_count,
            len(assistant_response), len(vault_context) if vault_context else 0,
        )
        try:
            await extract_learnings(
                self.vault, self.config, self.model,
                user_message, assistant_response, vault_context,
                usage_tracker=self._usage_tracker,
                agent_id=self.agent_id, org_id=self._org_id,
                conversation_id=conversation_id,
            )
            logger.debug("[%s] 📝 LEARN COMPLETE — turn #%d", self.agent_id, self._turn_count)
            if self._turn_count % self.config.consolidation_interval == 0:
                logger.debug(
                    "[%s] 🔄 CONSOLIDATION triggered at turn #%d",
                    self.agent_id, self._turn_count,
                )
                await self.consolidate()
        except Exception as e:
            logger.warning("MemoryManager process_turn failed: %s", e)

    async def link_outcome(
        self,
        outcome_path: str,
        related_paths: list[str],
        outcome_type: str,
    ) -> str:
        """Link a known outcome to prior decisions and update confidence."""
        logger.debug(
            "[%s] 🔗 OUTCOME LINK — type=%s, outcome=%s, related=%s",
            self.agent_id, outcome_type, outcome_path, related_paths,
        )
        result = await link_outcome(self.vault, outcome_path, related_paths, outcome_type)
        logger.debug("[%s] 🔗 OUTCOME LINK RESULT — %s", self.agent_id, result)
        return result

    async def consolidate(self) -> None:
        """Lightweight consolidation — expire short-term, decay long-term."""
        # Expire short-term memories past TTL
        expired = self._expire_short_term()
        if expired:
            logger.info("[%s] Expired %d short-term memories to deep", self.agent_id, expired)

        # Decay confidence on long-term memories
        lt_entries = self.vault.list_branch("memory/long-term")
        if len(lt_entries) >= 3:
            apply_confidence_decay(self.vault, self.config, lt_entries)

        # Sink long-term memories below threshold to deep
        sunk = self._sink_decayed_long_term()
        if sunk:
            logger.info("[%s] Sunk %d decayed long-term memories to deep", self.agent_id, sunk)

        logger.debug("[%s] Consolidation complete", self.agent_id)

    async def deep_consolidate(self) -> None:
        """Run LLM-driven deep consolidation (called by scheduler)."""
        if not self.config.deep_consolidation_enabled:
            return
        from axon.vault.memory_consolidation import deep_consolidate

        report = await deep_consolidate(
            self.vault, self.config, self.model,
            usage_tracker=self._usage_tracker,
            agent_id=self.agent_id, org_id=self._org_id,
        )
        logger.info(
            "[%s] Deep consolidation: reviewed=%d, merged=%d, archived=%d, contradictions=%d",
            self.agent_id, report.entries_reviewed, report.llm_merged,
            report.llm_archived + report.auto_archived, report.contradictions_flagged,
        )

    # ── Memory lifecycle ─────────────────────────────────────────

    def promote_to_long_term(self, short_term_path: str) -> str | None:
        """Promote a short-term memory to long-term.

        Called when a short-term memory is referenced again or validated.
        Returns the new path, or None on failure.
        """
        try:
            metadata, body = self.vault.read_file(short_term_path)
            metadata["memory_tier"] = "long_term"
            metadata["confidence"] = max(
                float(metadata.get("confidence", 0.5)),
                self.config.promotion_confidence,
            )
            metadata["confidence_history"] = metadata.get("confidence_history", [])
            metadata["confidence_history"].append({
                "date": str(date.today()),
                "value": metadata["confidence"],
                "reason": "promoted from short-term",
            })
            metadata["last_validated"] = str(date.today())

            # Move file: memory/short-term/X.md -> memory/long-term/X.md
            filename = Path(short_term_path).name
            new_path = f"memory/long-term/{filename}"
            self.vault.write_file(new_path, metadata, body)
            self._remove_file(short_term_path)

            logger.info("[%s] Promoted %s -> %s", self.agent_id, short_term_path, new_path)
            return new_path
        except Exception as e:
            logger.warning("[%s] Failed to promote %s: %s", self.agent_id, short_term_path, e)
            return None

    def sink_to_deep(self, source_path: str) -> str | None:
        """Sink a memory (short-term or long-term) to deep memory.

        Forgotten memories live in deep/ until user review.
        Returns the new path, or None on failure.
        """
        try:
            metadata, body = self.vault.read_file(source_path)
            metadata["memory_tier"] = "deep"
            metadata["status"] = "archived"
            metadata["sunk_from"] = source_path
            metadata["sunk_date"] = str(date.today())

            filename = Path(source_path).name
            new_path = f"deep/{filename}"
            self.vault.write_file(new_path, metadata, body)
            self._remove_file(source_path)

            logger.info("[%s] Sunk %s -> %s", self.agent_id, source_path, new_path)
            return new_path
        except Exception as e:
            logger.warning("[%s] Failed to sink %s: %s", self.agent_id, source_path, e)
            return None

    def reinvigorate(self, deep_path: str) -> str | None:
        """Reinvigorate a deep memory back to long-term.

        Called when user approves during deep memory review.
        Returns the new path, or None on failure.
        """
        try:
            metadata, body = self.vault.read_file(deep_path)
            metadata["memory_tier"] = "long_term"
            metadata["status"] = "active"
            metadata["confidence"] = max(float(metadata.get("confidence", 0.3)), 0.5)
            metadata["confidence_history"] = metadata.get("confidence_history", [])
            metadata["confidence_history"].append({
                "date": str(date.today()),
                "value": metadata["confidence"],
                "reason": "reinvigorated by user from deep memory",
            })
            metadata["last_validated"] = str(date.today())
            metadata.pop("sunk_from", None)
            metadata.pop("sunk_date", None)

            filename = Path(deep_path).name
            new_path = f"memory/long-term/{filename}"
            self.vault.write_file(new_path, metadata, body)
            self._remove_file(deep_path)

            logger.info("[%s] Reinvigorated %s -> %s", self.agent_id, deep_path, new_path)
            return new_path
        except Exception as e:
            logger.warning("[%s] Failed to reinvigorate %s: %s", self.agent_id, deep_path, e)
            return None

    def list_deep_for_review(self) -> list[dict[str, Any]]:
        """List deep memories available for user review."""
        return self.vault.list_branch("deep")

    def delete_deep_memory(self, deep_path: str) -> bool:
        """Permanently delete a deep memory (user-approved deletion)."""
        try:
            self._remove_file(deep_path)
            logger.info("[%s] Permanently deleted %s", self.agent_id, deep_path)
            return True
        except Exception as e:
            logger.warning("[%s] Failed to delete %s: %s", self.agent_id, deep_path, e)
            return False

    def archive_conversation(self, conversation_id: str, messages: list[dict], title: str = "") -> str | None:
        """Archive a conversation to the vault's conversations tree."""
        from axon.vault.conversation_archive import archive_conversation
        return archive_conversation(
            self.vault.vault_path, conversation_id, messages,
            agent_id=self.agent_id, title=title,
        )

    # ── Internal helpers ─────────────────────────────────────────

    def _expire_short_term(self) -> int:
        """Move expired short-term memories to deep. Returns count moved."""
        st_entries = self.vault.list_branch("memory/short-term")
        cutoff = date.today() - timedelta(days=self.config.short_term_ttl_days)
        expired = 0

        for entry in st_entries:
            path = entry.get("path", "")
            entry_date = entry.get("date", "")
            if not path or not entry_date:
                continue
            try:
                if date.fromisoformat(entry_date) <= cutoff:
                    if self.sink_to_deep(path):
                        expired += 1
            except (ValueError, TypeError):
                continue

        return expired

    def _sink_decayed_long_term(self) -> int:
        """Sink long-term memories below confidence threshold to deep."""
        lt_entries = self.vault.list_branch("memory/long-term")
        threshold = self.config.archive_confidence_threshold
        sunk = 0

        for entry in lt_entries:
            path = entry.get("path", "")
            confidence = entry.get("confidence", 0.5)
            if not path:
                continue
            try:
                if float(confidence) < threshold:
                    if self.sink_to_deep(path):
                        sunk += 1
            except (ValueError, TypeError):
                continue

        return sunk

    def _remove_file(self, relative_path: str) -> None:
        """Remove a file from the vault filesystem."""
        full_path = self.vault.vault_path / relative_path
        if full_path.exists():
            full_path.unlink()
            # Invalidate cache/graph
            if self.vault._cache:
                self.vault._cache.invalidate(relative_path)
            self.vault._graph = None

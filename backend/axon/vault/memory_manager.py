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
import shutil
from datetime import date, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

from axon.config import LearningConfig
from axon.logging import get_logger
from axon.vault.frontmatter import parse_frontmatter, write_frontmatter
from axon.vault.memory_recall import recall_with_llm, recall_fallback
from axon.vault.memory_learning import extract_learnings, link_outcome, apply_confidence_decay
from axon.vault.vault import VaultManager

if TYPE_CHECKING:
    from axon.usage import UsageTracker
    from axon.vault.vector_store import VaultVectorStore

logger = get_logger(__name__)


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
        vector_store: "VaultVectorStore | None" = None,
    ):
        self.vault = vault
        self.config = config
        self.model = model
        self.agent_id = agent_id
        self._usage_tracker = usage_tracker
        self._org_id = org_id
        self._turn_count = 0
        self._vector_store = vector_store
        self._log = logger.bind(agent_id=agent_id, org_id=org_id)

    async def recall(self, user_message: str) -> str:
        """Retrieve relevant vault context for a user message."""
        self._log.debug("recall_start", message_preview=user_message[:80])
        try:
            result = await recall_with_llm(
                self.vault, self.config, self.model, user_message,
                usage_tracker=self._usage_tracker,
                agent_id=self.agent_id, org_id=self._org_id,
                vector_store=self._vector_store,
            )
            self._log.debug("recall_complete", chars=len(result))
            return result
        except TimeoutError:
            self._log.warning("recall_timeout", fallback="deterministic")
            return await asyncio.to_thread(recall_fallback, self.vault, self.config, user_message)
        except Exception as e:
            self._log.warning("recall_failed", fallback="deterministic", error=str(e))
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
        self._log.debug(
            "learn_start", turn=self._turn_count,
            response_chars=len(assistant_response),
            context_chars=len(vault_context) if vault_context else 0,
        )
        try:
            await extract_learnings(
                self.vault, self.config, self.model,
                user_message, assistant_response, vault_context,
                usage_tracker=self._usage_tracker,
                agent_id=self.agent_id, org_id=self._org_id,
                conversation_id=conversation_id,
            )
            self._log.debug("learn_complete", turn=self._turn_count)
            # Index new/updated memories in vector store
            await self._index_recent_memories()
            if self._turn_count % self.config.consolidation_interval == 0:
                self._log.debug("consolidation_triggered", turn=self._turn_count)
                await self.consolidate()
        except Exception as e:
            self._log.warning("learn_failed", error=str(e))

    async def link_outcome(
        self,
        outcome_path: str,
        related_paths: list[str],
        outcome_type: str,
    ) -> str:
        """Link a known outcome to prior decisions and update confidence."""
        self._log.debug(
            "outcome_link", outcome_type=outcome_type,
            outcome_path=outcome_path, related_paths=related_paths,
        )
        result = await link_outcome(self.vault, outcome_path, related_paths, outcome_type)
        self._log.debug("outcome_link_result", result=result)
        return result

    async def consolidate(self) -> None:
        """Lightweight consolidation — expire short-term, decay long-term."""
        expired = self._expire_short_term()
        if expired:
            self._log.info("memories_expired", count=expired, tier="short_term")

        lt_entries = self.vault.list_branch("memory/long-term")
        if len(lt_entries) >= 3:
            apply_confidence_decay(self.vault, self.config, lt_entries)

        sunk = self._sink_decayed_long_term()
        if sunk:
            self._log.info("memories_sunk", count=sunk, tier="long_term")

        self._log.debug("consolidation_complete")

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
        self._log.info(
            "deep_consolidation_complete",
            reviewed=report.entries_reviewed, merged=report.llm_merged,
            archived=report.llm_archived + report.auto_archived,
            contradictions=report.contradictions_flagged,
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

            self._log.info("memory_promoted", src=short_term_path, dst=new_path)
            self._schedule_vector_update(self._vector_upsert(new_path, metadata, body))
            self._schedule_vector_update(self._vector_remove(short_term_path))
            return new_path
        except Exception as e:
            self._log.warning("memory_promote_failed", path=short_term_path, error=str(e))
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

            self._log.info("memory_sunk", src=source_path, dst=new_path)
            self._schedule_vector_update(self._vector_remove(source_path))
            return new_path
        except Exception as e:
            self._log.warning("memory_sink_failed", path=source_path, error=str(e))
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

            self._log.info("memory_reinvigorated", src=deep_path, dst=new_path)
            self._schedule_vector_update(self._vector_upsert(new_path, metadata, body))
            self._schedule_vector_update(self._vector_remove(deep_path))
            return new_path
        except Exception as e:
            self._log.warning("memory_reinvigorate_failed", path=deep_path, error=str(e))
            return None

    def list_deep_for_review(self) -> list[dict[str, Any]]:
        """List deep memories available for user review."""
        return self.vault.list_branch("deep")

    def delete_deep_memory(self, deep_path: str) -> bool:
        """Permanently delete a deep memory (user-approved deletion)."""
        try:
            self._remove_file(deep_path)
            self._log.info("memory_deleted", path=deep_path)
            self._schedule_vector_update(self._vector_remove(deep_path))
            return True
        except Exception as e:
            self._log.warning("memory_delete_failed", path=deep_path, error=str(e))
            return False

    def archive_conversation(self, conversation_id: str, messages: list[dict], title: str = "") -> str | None:
        """Archive a conversation to the vault's conversations tree."""
        from axon.vault.conversation_archive import archive_conversation
        return archive_conversation(
            self.vault.vault_path, conversation_id, messages,
            agent_id=self.agent_id, title=title,
        )

    # ── Vector store helpers ───────────────────────────────────────

    def _schedule_vector_update(self, coro) -> None:
        """Schedule an async vector operation from a sync context."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(coro)
        except RuntimeError:
            # No running loop — skip vector update silently
            pass

    async def _vector_upsert(
        self, path: str, metadata: dict[str, Any], body: str,
    ) -> None:
        """Index a memory entry in the vector store (no-op if disabled)."""
        if not self._vector_store:
            return
        try:
            tier = metadata.get("memory_tier", "")
            name = metadata.get("name", Path(path).stem)
            await self._vector_store.upsert(path, name, tier, body)
        except Exception as e:
            self._log.warning("vector_upsert_failed", path=path, error=str(e))

    async def _vector_remove(self, path: str) -> None:
        """Remove a memory entry from the vector store (no-op if disabled)."""
        if not self._vector_store:
            return
        try:
            await self._vector_store.remove(path)
        except Exception as e:
            self._log.warning("vector_remove_failed", path=path, error=str(e))

    async def _index_recent_memories(self) -> None:
        """Index the most recent short-term memories in the vector store."""
        if not self._vector_store:
            return
        try:
            st_entries = self.vault.list_branch("memory/short-term")
            for entry in st_entries[-5:]:  # last 5 (most recent)
                path = entry.get("path", "")
                if not path:
                    continue
                try:
                    metadata, body = self.vault.read_file(path)
                    await self._vector_upsert(path, metadata, body)
                except Exception:
                    pass
        except Exception as e:
            self._log.debug("vector_index_recent_failed", error=str(e))

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

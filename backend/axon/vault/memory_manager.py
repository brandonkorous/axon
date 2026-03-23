"""MemoryManager — local-LLM-powered memory for agent vaults.

Sits on both sides of the paid reasoning model:
- INBOUND:  recall() semantically searches the vault before the paid model sees the message
- OUTBOUND: process_turn() extracts learnings after the paid model responds

Uses a cheap local model (e.g. ollama/llama3:8b) for all memory work.
Falls back to deterministic MemoryNavigator if the local model is unavailable.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from axon.config import LearningConfig
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
            return recall_fallback(self.vault, self.config, user_message)
        except Exception as e:
            logger.warning("[%s] MemoryManager recall failed — using fallback: %s", self.agent_id, e)
            return recall_fallback(self.vault, self.config, user_message)

    async def process_turn(
        self,
        user_message: str,
        assistant_response: str,
        vault_context: str,
    ) -> None:
        """Process a completed turn — extract and store learnings."""
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
        """Consolidate scattered learnings — apply confidence decay."""
        learnings = self.vault.list_branch("learnings")
        logger.debug(
            "[%s] 🔄 CONSOLIDATE — %d learnings in vault",
            self.agent_id, len(learnings),
        )
        if len(learnings) < 3:
            logger.debug("[%s] 🔄 CONSOLIDATE skipped — fewer than 3 learnings", self.agent_id)
            return
        apply_confidence_decay(self.vault, self.config, learnings)
        logger.debug("[%s] 🔄 CONSOLIDATE done — confidence decay applied", self.agent_id)

"""ExternalAgent — a bridge agent backed by a host-side runner, not an LLM."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator

from axon.agents.agent import Agent, StreamChunk
from axon.agents.conversation import ConversationManager
from axon.config import PersonaConfig
from axon.lifecycle import AgentLifecycle
from axon.vault.vault import VaultManager

logger = logging.getLogger(__name__)


class ExternalAgent(Agent):
    """An agent backed by an external process (e.g. Claude Code on the host).

    Sits in the registry so delegation and get_agent() work normally.
    Does NOT call an LLM — incoming tasks are picked up by the host-side
    runner via the external agent REST API.
    """

    is_external = True

    def __init__(
        self,
        config: PersonaConfig,
        data_dir: str = "/data",
        shared_vault: VaultManager | None = None,
        audit_logger: "AuditLogger | None" = None,
        usage_tracker: "UsageTracker | None" = None,
        org_id: str = "",
    ):
        # Minimal init — vault and lifecycle only, no LLM/memory/tools
        self.config = config
        self.id = config.id
        self.name = config.name
        self.org_id = org_id

        self.vault = VaultManager(config.vault.path, config.vault.root_file)
        self.shared_vault = shared_vault

        # Conversations and lifecycle (for consistency with Agent interface)
        self.conversation_manager = ConversationManager(agent_id=self.id, data_dir=data_dir)
        state_dir = str(Path(data_dir) / "agent-state")
        self.lifecycle = AgentLifecycle.load(self.id, state_dir)

        # Heartbeat — updated each time the runner polls for tasks
        self.last_poll_time: datetime | None = None

        # No LLM, no memory, no tools
        self.navigator = None
        self.memory_manager = None
        self.tool_executor = None
        self.tools = []
        self._system_prompt = ""

        logger.info("[%s] ExternalAgent initialized (host-side runner)", config.id)

    async def process(
        self, user_message: str, *, save_history: bool = True,
    ) -> AsyncIterator[StreamChunk]:
        """External agents don't process messages via LLM.

        Tasks arrive in the vault inbox and are picked up by the runner.
        """
        yield StreamChunk(
            agent_id=self.id,
            type="text",
            content=(
                f"*Task queued for external agent **{self.name}**. "
                f"The host-side runner will pick this up shortly.*"
            ),
        )
        yield StreamChunk(agent_id=self.id, type="done")

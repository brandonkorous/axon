"""Global agent registry — breaks circular imports between main.py and routes."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from axon.agents.agent import Agent
    from axon.agents.boardroom import Boardroom

agent_registry: dict[str, "Agent"] = {}
boardroom_instance: "Boardroom | None" = None

"""WebSocket connection registry — enables server-push to active clients.

Maps (agent_id, conversation_id) → set of WebSocket connections so the
scheduler can push task results back to the correct conversation.
"""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from fastapi import WebSocket

from axon.logging import get_logger

logger = get_logger(__name__)

# (agent_id, conversation_id) → set of connected WebSockets
_connections: dict[tuple[str, str], set[WebSocket]] = defaultdict(set)


def register(agent_id: str, conversation_id: str, ws: WebSocket) -> None:
    """Register a WebSocket for a specific agent conversation."""
    _connections[(agent_id, conversation_id)].add(ws)
    logger.debug("[WS_REG] Registered %s/%s (total: %d)", agent_id, conversation_id,
                 len(_connections[(agent_id, conversation_id)]))


def unregister(agent_id: str, conversation_id: str, ws: WebSocket) -> None:
    """Unregister a WebSocket. Safe to call even if not registered."""
    key = (agent_id, conversation_id)
    _connections[key].discard(ws)
    if not _connections[key]:
        del _connections[key]


async def push(agent_id: str, conversation_id: str, message: dict[str, Any]) -> int:
    """Send a JSON message to all connected clients for this conversation.

    Returns the number of clients that received the message.
    Dead connections are silently removed.
    """
    key = (agent_id, conversation_id)
    clients = _connections.get(key)
    if not clients:
        return 0

    sent = 0
    dead: list[WebSocket] = []
    payload = json.dumps(message)

    for ws in clients:
        try:
            await ws.send_text(payload)
            sent += 1
        except Exception:
            dead.append(ws)

    for ws in dead:
        clients.discard(ws)
    if not clients:
        del _connections[key]

    return sent

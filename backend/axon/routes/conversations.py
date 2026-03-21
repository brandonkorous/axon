"""Conversation routes — chat via WebSocket with streaming."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException

from axon.main import agent_registry

router = APIRouter()


@router.websocket("/ws/{agent_id}")
async def conversation_websocket(websocket: WebSocket, agent_id: str):
    """WebSocket endpoint for streaming conversations with an agent.

    Client sends: { "type": "message", "content": "..." }
    Server sends:
      { "type": "thinking", "agent_id": "..." }
      { "type": "text", "agent_id": "...", "content": "..." }
      { "type": "tool_use", "agent_id": "...", "content": "...", "metadata": {...} }
      { "type": "route", "agent_id": "...", "metadata": { "target_agent": "..." } }
      { "type": "boardroom", "agent_id": "...", "metadata": { "topic": "...", "mode": "..." } }
      { "type": "done", "agent_id": "..." }
    """
    agent = agent_registry.get(agent_id)
    if not agent:
        await websocket.close(code=4004, reason=f"Agent not found: {agent_id}")
        return

    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "message":
                user_content = message.get("content", "")
                if not user_content:
                    continue

                target_agent = agent
                routed = False

                # Check for @mention to bypass Axon routing
                if user_content.startswith("@"):
                    parts = user_content.split(" ", 1)
                    mentioned = parts[0][1:].lower()
                    if mentioned in agent_registry:
                        target_agent = agent_registry[mentioned]
                        user_content = parts[1] if len(parts) > 1 else ""
                        routed = True

                # Process through the agent
                async for chunk in target_agent.process(user_content):
                    response = {
                        "type": chunk.type,
                        "agent_id": chunk.agent_id,
                        "content": chunk.content,
                    }
                    if chunk.metadata:
                        response["metadata"] = chunk.metadata

                    # Handle routing — switch to target agent
                    if chunk.type == "route" and chunk.metadata:
                        target_id = chunk.metadata.get("target_agent")
                        routed_agent = agent_registry.get(target_id)
                        if routed_agent:
                            await websocket.send_json(response)
                            # Process through the routed agent
                            context = chunk.metadata.get("context", "")
                            routed_message = f"{context}\n\n{user_content}" if context else user_content
                            async for sub_chunk in routed_agent.process(routed_message):
                                await websocket.send_json({
                                    "type": sub_chunk.type,
                                    "agent_id": sub_chunk.agent_id,
                                    "content": sub_chunk.content,
                                    **({"metadata": sub_chunk.metadata} if sub_chunk.metadata else {}),
                                })
                            continue

                    await websocket.send_json(response)

            elif message.get("type") == "greeting":
                # Generate first-message greeting
                async for chunk in agent.generate_greeting():
                    await websocket.send_json({
                        "type": chunk.type,
                        "agent_id": chunk.agent_id,
                        "content": chunk.content,
                    })

            elif message.get("type") == "clear":
                agent.conversation.clear()
                await websocket.send_json({"type": "cleared"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "content": str(e)})
        except Exception:
            pass


@router.get("/{agent_id}/history")
async def get_conversation_history(agent_id: str):
    """Get conversation history for an agent."""
    agent = agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    return {
        "agent_id": agent_id,
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "agent_id": m.agent_id,
                "timestamp": m.timestamp,
            }
            for m in agent.conversation.messages
        ],
    }

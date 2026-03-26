"""Huddle routes — multi-persona advisory sessions via WebSocket."""

from __future__ import annotations

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException

import axon.registry as registry
import axon.ws_registry as ws_registry
from axon.agents.huddle import split_response_by_speaker

router = APIRouter()
org_router = APIRouter()


def _build_history(messages) -> list[dict]:
    """Build history with per-speaker messages for assistant messages."""
    history: list[dict] = []
    for m in messages:
        if m.role == "assistant" and m.agent_id and m.agent_id != "huddle":
            # New per-advisor format: each message is already one speaker
            history.append({
                "role": "assistant",
                "content": m.content,
                "speaker": m.agent_id,
                "target": None,
                "timestamp": m.timestamp,
            })
        elif m.role == "assistant":
            # Legacy combined format — fall back to regex split
            history.extend(split_response_by_speaker(m.content, m.timestamp))
        else:
            history.append({
                "role": m.role,
                "content": m.content,
                "speaker": None,
                "target": None,
                "timestamp": m.timestamp,
            })
    return history


async def _handle_huddle(websocket: WebSocket, huddle):
    """Shared huddle WebSocket handler.

    Client sends:
      { "type": "message", "content": "...", "mode": "standard" }
      { "type": "clear" }
      { "type": "switch", "conversation_id": "..." }

    Server sends (pushed directly by advisor tasks via ws_registry):
      { "type": "thinking", "speaker": "marcus" }       — advisor started processing
      { "type": "text", "speaker": "marcus", "content": "..." }  — streamed text
      { "type": "speaker_done", "speaker": "marcus" }   — advisor finished
      { "type": "done" }                                 — all advisors finished
      { "type": "switched", "conversation_id": "...", "messages": [...] }
    """
    await websocket.accept()

    if not huddle:
        await websocket.send_json({"type": "error", "content": "Huddle not configured"})
        await websocket.close(code=4004, reason="Huddle not configured")
        return
    active_conv_id = huddle.conversation_manager.active_id
    ws_registry.register("huddle", active_conv_id, websocket)

    # Send existing conversation history on connect
    await websocket.send_json({
        "type": "switched",
        "conversation_id": active_conv_id,
        "messages": _build_history(huddle.conversation.messages),
    })

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "message":
                content = message.get("content", "")
                mode = message.get("mode", "standard")

                # Auto-title from first user message
                mgr = huddle.conversation_manager
                mgr.auto_title_from_message(mgr.active_id, content)

                # Dispatch to advisors — each streams directly via ws_registry
                await huddle.dispatch(content, mode=mode)

            elif message.get("type") == "clear":
                huddle.conversation.clear()
                await websocket.send_json({"type": "cleared"})

            elif message.get("type") == "switch":
                conv_id = message.get("conversation_id", "")
                if not conv_id:
                    await websocket.send_json({"type": "error", "content": "Missing conversation_id"})
                    continue
                old_conv_id = active_conv_id
                try:
                    huddle.conversation_manager.switch(conv_id)
                    new_conv_id = huddle.conversation_manager.active_id
                    if new_conv_id != old_conv_id:
                        ws_registry.unregister("huddle", old_conv_id, websocket)
                        ws_registry.register("huddle", new_conv_id, websocket)
                        active_conv_id = new_conv_id
                    await websocket.send_json({
                        "type": "switched",
                        "conversation_id": conv_id,
                        "messages": _build_history(huddle.conversation.messages),
                    })
                except ValueError:
                    await websocket.send_json({
                        "type": "error",
                        "content": f"Conversation not found: {conv_id}",
                    })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "content": str(e)})
        except Exception:
            pass
    finally:
        ws_registry.unregister("huddle", active_conv_id, websocket)


def _get_huddle_history(huddle) -> dict:
    """Build history response for a huddle."""
    if not huddle:
        return {"messages": []}
    return {"messages": _build_history(huddle.conversation.messages)}


# ── Legacy routes (default org) ─────────────────────────────────────


@router.websocket("/ws")
async def huddle_websocket(websocket: WebSocket):
    """WebSocket endpoint for huddle sessions (default org)."""
    await _handle_huddle(websocket, registry.huddle_instance)


@router.get("/history")
async def get_huddle_history():
    """Get huddle conversation history."""
    return _get_huddle_history(registry.huddle_instance)


@router.get("/conversations")
async def list_huddle_conversations():
    """List all huddle conversations."""
    huddle = registry.huddle_instance
    if not huddle:
        raise HTTPException(status_code=404, detail="Huddle not configured")
    return {
        "conversations": huddle.conversation_manager.list_conversations(),
        "active_id": huddle.conversation_manager.active_id,
    }


@router.post("/conversations")
async def create_huddle_conversation():
    """Create a new huddle conversation."""
    huddle = registry.huddle_instance
    if not huddle:
        raise HTTPException(status_code=404, detail="Huddle not configured")
    conv_id = huddle.conversation_manager.create_new()
    return {"conversation_id": conv_id}


@router.delete("/conversations/{conversation_id}")
async def delete_huddle_conversation(conversation_id: str):
    """Delete a huddle conversation."""
    huddle = registry.huddle_instance
    if not huddle:
        raise HTTPException(status_code=404, detail="Huddle not configured")
    deleted = huddle.conversation_manager.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Conversation not found: {conversation_id}")
    return {"deleted": True, "active_id": huddle.conversation_manager.active_id}


# ── Org-scoped routes ───────────────────────────────────────────────


@org_router.websocket("/ws")
async def org_huddle_websocket(websocket: WebSocket, org_id: str):
    """WebSocket endpoint for huddle sessions (org-scoped)."""
    huddle = registry.get_huddle(org_id)
    await _handle_huddle(websocket, huddle)


@org_router.get("/history")
async def get_org_huddle_history(org_id: str):
    """Get huddle conversation history (org-scoped)."""
    huddle = registry.get_huddle(org_id)
    return _get_huddle_history(huddle)


@org_router.get("/conversations")
async def list_org_huddle_conversations(org_id: str):
    """List all huddle conversations (org-scoped)."""
    huddle = registry.get_huddle(org_id)
    if not huddle:
        return {"conversations": [], "active_id": None}
    return {
        "conversations": huddle.conversation_manager.list_conversations(),
        "active_id": huddle.conversation_manager.active_id,
    }


@org_router.post("/conversations")
async def create_org_huddle_conversation(org_id: str):
    """Create a new huddle conversation (org-scoped)."""
    huddle = registry.get_huddle(org_id)
    if not huddle:
        raise HTTPException(status_code=404, detail="Huddle not configured")
    conv_id = huddle.conversation_manager.create_new()
    return {"conversation_id": conv_id}


@org_router.delete("/conversations/{conversation_id}")
async def delete_org_huddle_conversation(org_id: str, conversation_id: str):
    """Delete a huddle conversation (org-scoped)."""
    huddle = registry.get_huddle(org_id)
    if not huddle:
        raise HTTPException(status_code=404, detail="Huddle not configured")
    deleted = huddle.conversation_manager.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Conversation not found: {conversation_id}")
    return {"deleted": True, "active_id": huddle.conversation_manager.active_id}

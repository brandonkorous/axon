"""Boardroom routes — multi-persona advisory sessions via WebSocket."""

from __future__ import annotations

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from axon.main import boardroom_instance

router = APIRouter()


@router.websocket("/ws")
async def boardroom_websocket(websocket: WebSocket):
    """WebSocket endpoint for boardroom sessions.

    Client sends:
      { "type": "message", "content": "...", "mode": "standard" }

    Server sends:
      { "type": "thinking" }
      { "type": "text", "speaker": "marcus", "target": null, "content": "..." }
      { "type": "text", "speaker": "raj", "target": "marcus", "content": "..." }
      { "type": "text", "speaker": "table", "target": null, "content": "..." }
      { "type": "done" }
    """
    if not boardroom_instance:
        await websocket.close(code=4004, reason="Boardroom not configured")
        return

    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "message":
                content = message.get("content", "")
                mode = message.get("mode", "standard")

                async for chunk in boardroom_instance.process(content, mode=mode):
                    await websocket.send_json({
                        "type": chunk.type,
                        "speaker": chunk.speaker,
                        "target": chunk.target,
                        "content": chunk.content,
                    })

            elif message.get("type") == "clear":
                boardroom_instance.conversation.clear()
                await websocket.send_json({"type": "cleared"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "content": str(e)})
        except Exception:
            pass


@router.get("/history")
async def get_boardroom_history():
    """Get boardroom conversation history."""
    if not boardroom_instance:
        return {"messages": []}

    return {
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp,
            }
            for m in boardroom_instance.conversation.messages
        ],
    }

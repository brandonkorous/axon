"""Conversation routes — chat via WebSocket with streaming."""

from __future__ import annotations

import asyncio
import base64
import json
import mimetypes
import re
import time
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File

from axon.logging import get_logger
import axon.registry as registry
import axon.ws_registry as ws_registry

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB per file
ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp"}

logger = get_logger("axon.conversations")

router = APIRouter()
org_router = APIRouter()


async def _handle_conversation(websocket: WebSocket, agent_reg: dict, agent_id: str):
    """Shared WebSocket conversation handler.

    Client sends:
      { "type": "message", "content": "..." }
      { "type": "command", "name": "...", "args": "..." }
      { "type": "audio", "audio": "<base64 PCM>", "sample_rate": 16000 }
      { "type": "greeting" }
      { "type": "clear" }
      { "type": "switch", "conversation_id": "..." }

    Server sends:
      { "type": "thinking", "agent_id": "..." }
      { "type": "text", "agent_id": "...", "content": "..." }
      { "type": "tool_use", "agent_id": "...", "content": "...", "metadata": {...} }
      { "type": "route", "agent_id": "...", "metadata": { "target_agent": "..." } }
      { "type": "huddle", "agent_id": "...", "metadata": { "topic": "...", "mode": "..." } }
      { "type": "done", "agent_id": "..." }
      { "type": "transcription", "content": "..." }
      { "type": "audio_response", "audio": "<base64 WAV>", "agent_id": "..." }
      { "type": "switched", "conversation_id": "...", "messages": [...] }
      { "type": "command_result", "agent_id": "...", "command": "...", "content": "...", "success": true }
    """
    await websocket.accept()

    agent = agent_reg.get(agent_id)
    if not agent:
        await websocket.send_json({"type": "error", "content": f"Agent not found: {agent_id}"})
        await websocket.close(code=4004, reason=f"Agent not found: {agent_id}")
        return

    # Track active conversation for ws_registry
    active_conv_id = agent.conversation_manager.active_id
    ws_registry.register(agent_id, active_conv_id, websocket)

    # Send existing conversation history on connect (skip "tool" role — LLM-only context)
    history = [
        {
            "role": m.role,
            "content": m.content,
            "agent_id": m.agent_id,
            "timestamp": m.timestamp,
            **({"metadata": m.metadata} if m.metadata else {}),
        }
        for m in agent.conversation.messages
        if m.role != "tool"
    ]
    await websocket.send_json({
        "type": "switched",
        "conversation_id": active_conv_id,
        "messages": history,
    })

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "message":
                user_content = message.get("content", "")
                attachments = message.get("attachments", []) or []
                if not user_content and not attachments:
                    continue

                # Auto-title from first user message
                mgr = agent.conversation_manager
                if user_content:
                    mgr.auto_title_from_message(mgr.active_id, user_content)

                want_audio = message.get("voice", False)
                await _process_and_stream(
                    websocket, agent, agent_reg, user_content, want_audio,
                    attachments=attachments,
                )

            elif message.get("type") == "audio":
                # Speech-to-text + process
                audio_b64 = message.get("audio", "")
                sample_rate = message.get("sample_rate", 16000)
                audio_format = message.get("format", "pcm")
                if not audio_b64:
                    continue

                try:
                    from axon.voice import transcribe

                    audio_bytes = base64.b64decode(audio_b64)
                    logger.debug(f"Transcribing {len(audio_bytes)} bytes (format={audio_format}, rate={sample_rate})")
                    # Run blocking STT in thread pool to avoid freezing the event loop
                    text = await asyncio.to_thread(
                        transcribe,
                        audio_bytes,
                        sample_rate=sample_rate,
                        audio_format=audio_format,
                    )
                    logger.debug(f"Transcription result: '{text}'")

                    if not text:
                        await websocket.send_json({
                            "type": "transcription",
                            "content": "",
                        })
                        continue

                    # Send transcription back to client
                    await websocket.send_json({
                        "type": "transcription",
                        "content": text,
                    })

                    # Process through agent with TTS response
                    await _process_and_stream(
                        websocket, agent, agent_reg, text,
                        want_audio=True,
                        voice_id_override=message.get("voice_id"),
                    )

                except ImportError:
                    await websocket.send_json({
                        "type": "error",
                        "content": "Voice features not available. Install with: pip install axon[voice]",
                    })
                except Exception as e:
                    logger.error(f"Voice processing error: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "content": f"Voice error: {e}",
                    })

            elif message.get("type") == "command":
                cmd_name = message.get("name", "")
                cmd_args = message.get("args", "")
                await _handle_command(websocket, agent, cmd_name, cmd_args)

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

            elif message.get("type") == "switch":
                old_conv_id = active_conv_id
                await _handle_switch(websocket, agent, message)
                # Update registry if switch succeeded
                new_conv_id = agent.conversation_manager.active_id
                if new_conv_id != old_conv_id:
                    ws_registry.unregister(agent_id, old_conv_id, websocket)
                    ws_registry.register(agent_id, new_conv_id, websocket)
                    active_conv_id = new_conv_id

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "content": str(e)})
        except Exception:
            pass
    finally:
        ws_registry.unregister(agent_id, active_conv_id, websocket)


async def _handle_command(websocket: WebSocket, agent, name: str, args: str):
    """Handle a slash command — execute directly without LLM."""
    from axon.commands.slash_commands import execute_command

    try:
        await execute_command(agent, name, args, websocket)
    except Exception as e:
        logger.error("Slash command /%s failed: %s", name, e, exc_info=True)
        await websocket.send_json({
            "type": "command_result",
            "agent_id": agent.id,
            "command": name,
            "content": f"Command error: {e}",
            "success": False,
        })


async def _handle_switch(websocket: WebSocket, agent, message: dict):
    """Handle conversation switching over WebSocket."""
    conv_id = message.get("conversation_id", "")
    if not conv_id:
        await websocket.send_json({"type": "error", "content": "Missing conversation_id"})
        return

    # Don't switch while agent is processing
    if hasattr(agent, "_processing_lock") and agent._processing_lock.locked():
        await websocket.send_json({
            "type": "error",
            "content": "Cannot switch while agent is responding",
        })
        return

    try:
        agent.conversation_manager.switch(conv_id)
        history = [
            {
                "role": m.role,
                "content": m.content,
                "agent_id": m.agent_id,
                "timestamp": m.timestamp,
                **({"metadata": m.metadata} if m.metadata else {}),
            }
            for m in agent.conversation.messages
            if m.role != "tool"
        ]
        await websocket.send_json({
            "type": "switched",
            "conversation_id": conv_id,
            "messages": history,
        })
    except ValueError:
        await websocket.send_json({
            "type": "error",
            "content": f"Conversation not found: {conv_id}",
        })


async def _process_and_stream(
    websocket: WebSocket,
    agent,
    agent_reg: dict,
    user_content: str,
    want_audio: bool = False,
    voice_id_override: str | None = None,
    attachments: list[dict] | None = None,
):
    """Process a message through the agent, stream text, optionally synthesize audio."""
    target_agent = agent

    # Check for @mention to bypass Axon routing
    if user_content.startswith("@"):
        parts = user_content.split(" ", 1)
        mentioned = parts[0][1:].lower()
        if mentioned in agent_reg:
            target_agent = agent_reg[mentioned]
            user_content = parts[1] if len(parts) > 1 else ""

    # Collect full response for TTS
    full_response = ""
    # Activity event types that should be persisted in conversation history
    PERSISTED_ACTIVITY_TYPES = {"tool_use", "agent_activated", "agent_result"}

    async for chunk in target_agent.process(user_content, attachments=attachments):
        response = {
            "type": chunk.type,
            "agent_id": chunk.agent_id,
            "content": chunk.content,
        }
        if chunk.metadata:
            response["metadata"] = chunk.metadata

        # Persist activity events so they survive refresh/switch
        if chunk.type in PERSISTED_ACTIVITY_TYPES:
            agent.conversation.add_system_message(
                chunk.content,
                metadata={"type": chunk.type, **(chunk.metadata or {})},
            )

        # Handle routing — switch to target agent
        if chunk.type == "route" and chunk.metadata:
            target_id = chunk.metadata.get("target_agent")
            routed_agent = agent_reg.get(target_id)
            if routed_agent:
                await websocket.send_json(response)
                context = chunk.metadata.get("context", "")
                routed_message = f"{context}\n\n{user_content}" if context else user_content
                async for sub_chunk in routed_agent.process(routed_message, attachments=attachments):
                    if sub_chunk.type == "text":
                        full_response += sub_chunk.content
                    # Persist activity events from routed agents too
                    if sub_chunk.type in PERSISTED_ACTIVITY_TYPES:
                        agent.conversation.add_system_message(
                            sub_chunk.content,
                            metadata={"type": sub_chunk.type, **(sub_chunk.metadata or {})},
                        )
                    await websocket.send_json({
                        "type": sub_chunk.type,
                        "agent_id": sub_chunk.agent_id,
                        "content": sub_chunk.content,
                        **({"metadata": sub_chunk.metadata} if sub_chunk.metadata else {}),
                    })
                continue

        if chunk.type == "text":
            full_response += chunk.content

        await websocket.send_json(response)

    # Synthesize TTS if requested and voice is configured
    if want_audio and full_response.strip():
        voice_config = getattr(target_agent.config, "voice", None)
        logger.debug(f"[TTS] check: want_audio={want_audio}, engine={voice_config.engine if voice_config else 'None'}")
        if voice_config and voice_config.engine != "disabled":
            try:
                from axon.voice import synthesize

                effective_voice = voice_id_override or voice_config.voice_id or "en_US-lessac-medium"
                logger.debug(f"[TTS] Synthesizing: {len(full_response)} chars, voice={effective_voice}")
                # Run blocking TTS in thread pool to avoid freezing the event loop
                audio_bytes = await asyncio.to_thread(
                    synthesize,
                    full_response,
                    voice_id=effective_voice,
                    speed=voice_config.speed,
                )
                logger.debug(f"TTS produced {len(audio_bytes)} bytes")
                audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
                await websocket.send_json({
                    "type": "audio_response",
                    "agent_id": target_agent.id,
                    "audio": audio_b64,
                })
                logger.debug("audio_response sent")
            except ImportError:
                logger.warning("Voice not installed — skipping TTS")
            except Exception as e:
                logger.error(f"TTS error: {e}", exc_info=True)


# ── Shared helpers for conversation list endpoints ─────────────────


def _conversation_list_response(agent):
    """Build conversation list response from an agent's ConversationManager."""
    return {
        "conversations": agent.conversation_manager.list_conversations(),
        "active_id": agent.conversation_manager.active_id,
    }


def _conversation_create_response(agent):
    """Create a new conversation and return response."""
    conv_id = agent.conversation_manager.create_new()
    return {"conversation_id": conv_id}


def _conversation_delete_response(agent, conversation_id: str):
    """Delete a conversation and return response."""
    deleted = agent.conversation_manager.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Conversation not found: {conversation_id}")
    return {"deleted": True, "active_id": agent.conversation_manager.active_id}


# ── File upload helper ─────────────────────────────────────────────


def _sanitize_filename(name: str) -> str:
    """Remove unsafe characters from a filename."""
    name = re.sub(r"[^\w.\-]", "_", name)
    return name[:200]  # cap length


async def _handle_upload(agent, file: UploadFile) -> dict:
    """Store an uploaded file and return its metadata."""
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(contents)} bytes). Max is {MAX_UPLOAD_SIZE} bytes.",
        )

    original_name = file.filename or "upload"
    content_type = file.content_type or mimetypes.guess_type(original_name)[0] or "application/octet-stream"
    sanitized = _sanitize_filename(original_name)
    stored_name = f"{int(time.time() * 1000)}_{sanitized}"

    data_dir: Path = agent.conversation_manager.data_dir
    attach_dir = data_dir / "attachments" / agent.id
    attach_dir.mkdir(parents=True, exist_ok=True)

    dest = attach_dir / stored_name
    dest.write_bytes(contents)

    relative_path = f"attachments/{agent.id}/{stored_name}"
    return {
        "path": relative_path,
        "name": original_name,
        "type": content_type,
        "size": len(contents),
    }


# ── Legacy routes (default org) ─────────────────────────────────────


@router.websocket("/ws/{agent_id}")
async def conversation_websocket(websocket: WebSocket, agent_id: str):
    """WebSocket endpoint for streaming conversations (default org)."""
    await _handle_conversation(websocket, registry.agent_registry, agent_id)


@router.post("/{agent_id}/upload")
async def upload_file(agent_id: str, file: UploadFile = File(...)):
    """Upload a file attachment for an agent (default org)."""
    agent = registry.agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return await _handle_upload(agent, file)


@router.get("/{agent_id}/history")
async def get_conversation_history(agent_id: str):
    """Get conversation history for an agent."""
    agent = registry.agent_registry.get(agent_id)
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
                **({"metadata": m.metadata} if m.metadata else {}),
            }
            for m in agent.conversation.messages
        ],
    }


@router.get("/{agent_id}/conversations")
async def list_conversations(agent_id: str):
    """List all conversations for an agent."""
    agent = registry.agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return _conversation_list_response(agent)


@router.post("/{agent_id}/conversations")
async def create_conversation(agent_id: str):
    """Create a new conversation for an agent."""
    agent = registry.agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return _conversation_create_response(agent)


@router.delete("/{agent_id}/conversations/{conversation_id}")
async def delete_conversation(agent_id: str, conversation_id: str):
    """Delete a conversation."""
    agent = registry.agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return _conversation_delete_response(agent, conversation_id)


# ── Org-scoped routes ───────────────────────────────────────────────


@org_router.websocket("/ws/{agent_id}")
async def org_conversation_websocket(websocket: WebSocket, org_id: str, agent_id: str):
    """WebSocket endpoint for streaming conversations (org-scoped)."""
    org = registry.get_org(org_id)
    if not org:
        await websocket.accept()
        await websocket.send_json({"type": "error", "content": f"Organization not found: {org_id}"})
        await websocket.close(code=4004, reason=f"Organization not found: {org_id}")
        return
    await _handle_conversation(websocket, org.agent_registry, agent_id)


@org_router.post("/{agent_id}/upload")
async def org_upload_file(org_id: str, agent_id: str, file: UploadFile = File(...)):
    """Upload a file attachment for an agent (org-scoped)."""
    agent = registry.get_agent(org_id, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id} in org {org_id}")
    return await _handle_upload(agent, file)


@org_router.get("/{agent_id}/history")
async def get_org_conversation_history(org_id: str, agent_id: str):
    """Get conversation history for an agent (org-scoped)."""
    agent = registry.get_agent(org_id, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id} in org {org_id}")

    return {
        "agent_id": agent_id,
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "agent_id": m.agent_id,
                "timestamp": m.timestamp,
                **({"metadata": m.metadata} if m.metadata else {}),
            }
            for m in agent.conversation.messages
        ],
    }


@org_router.get("/{agent_id}/conversations")
async def list_org_conversations(org_id: str, agent_id: str):
    """List all conversations for an agent (org-scoped)."""
    agent = registry.get_agent(org_id, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id} in org {org_id}")
    return _conversation_list_response(agent)


@org_router.post("/{agent_id}/conversations")
async def create_org_conversation(org_id: str, agent_id: str):
    """Create a new conversation for an agent (org-scoped)."""
    agent = registry.get_agent(org_id, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id} in org {org_id}")
    return _conversation_create_response(agent)


@org_router.delete("/{agent_id}/conversations/{conversation_id}")
async def delete_org_conversation(org_id: str, agent_id: str, conversation_id: str):
    """Delete a conversation (org-scoped)."""
    agent = registry.get_agent(org_id, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id} in org {org_id}")
    return _conversation_delete_response(agent, conversation_id)

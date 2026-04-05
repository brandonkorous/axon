"""Sandbox image management routes — build, status, and removal."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from axon.logging import get_logger
from axon.sandbox.builder import get_all_build_statuses, get_build_status
from axon.sandbox.manager import sandbox_manager
from axon.sandbox.types import (
    SANDBOX_METADATA,
    SANDBOX_PARENTS,
    SandboxType,
)

logger = get_logger(__name__)

org_router = APIRouter()


@org_router.get("")
async def list_sandbox_images(org_id: str):
    """List all sandbox image types with build status."""
    statuses = get_all_build_statuses()
    provider = sandbox_manager.provider
    result = []
    for stype in SandboxType:
        meta = SANDBOX_METADATA[stype]
        status = statuses.get(stype.value)
        parent = SANDBOX_PARENTS.get(stype)

        # If in-memory status is idle, check the runtime — the image may
        # already exist from a previous session or registry pull.
        state = status.state if status else "idle"
        size = status.size_mb if status else None
        if state == "idle" and await provider.image_exists(stype):
            state = "ready"
            size = await provider.get_image_size(stype)
            if status:
                status.state = "ready"
                status.size_mb = size

        result.append({
            "type": stype.value,
            "description": meta["description"],
            "estimated_size_mb": meta["estimated_size_mb"],
            "tools": meta["tools"],
            "parent_type": parent.value if parent else None,
            "status": state,
            "size_mb": size,
        })
    return {"images": result}


@org_router.get("/{image_type}")
async def get_sandbox_image_detail(org_id: str, image_type: str):
    """Get detailed info for a specific sandbox image type."""
    try:
        stype = SandboxType(image_type)
    except ValueError:
        raise HTTPException(404, f"Unknown sandbox type: {image_type}")

    provider = sandbox_manager.provider
    meta = SANDBOX_METADATA[stype]
    status = get_build_status(stype)
    parent = SANDBOX_PARENTS.get(stype)
    exists = await provider.image_exists(stype)
    size = await provider.get_image_size(stype) if exists else None

    # Sync in-memory status with runtime if stale
    if status.state == "idle" and exists:
        status.state = "ready"
        status.size_mb = size

    return {
        "type": stype.value,
        "description": meta["description"],
        "estimated_size_mb": meta["estimated_size_mb"],
        "tools": meta["tools"],
        "parent_type": parent.value if parent else None,
        "exists": exists,
        "size_mb": size,
        "status": status.state,
        "started_at": status.started_at.isoformat() if status.started_at else None,
        "completed_at": status.completed_at.isoformat() if status.completed_at else None,
        "error": status.error,
        "progress_lines": status.progress_lines[-20:],
    }


@org_router.post("/{image_type}/build")
async def trigger_build(org_id: str, image_type: str):
    """Trigger a background image build (or pull in registry mode)."""
    try:
        stype = SandboxType(image_type)
    except ValueError:
        raise HTTPException(404, f"Unknown sandbox type: {image_type}")

    status = get_build_status(stype)
    if status.state == "building":
        return {"status": "already_building", "type": stype.value}

    asyncio.create_task(_background_build(stype))
    return {"status": "build_started", "type": stype.value}


async def _background_build(stype: SandboxType) -> None:
    """Run image build/pull in background task."""
    try:
        await sandbox_manager.provider.ensure_image(stype)
    except Exception as e:
        logger.error("Background build failed for %s: %s", stype.value, e)


@org_router.websocket("/{image_type}/build/stream")
async def stream_build(websocket: WebSocket, image_type: str):
    """WebSocket endpoint for streaming build/pull progress."""
    try:
        stype = SandboxType(image_type)
    except ValueError:
        await websocket.close(code=4004, reason="Unknown sandbox type")
        return

    await websocket.accept()

    loop = asyncio.get_event_loop()

    def on_progress(line: str) -> None:
        """Non-async callback — schedule WS send on the event loop."""
        try:
            future = asyncio.run_coroutine_threadsafe(
                websocket.send_json({"type": "progress", "line": line}),
                loop,
            )
            future.result(timeout=5)
        except Exception:
            pass

    try:
        ok = await sandbox_manager.provider.ensure_image(stype, on_progress=on_progress)
        msg_type = "complete" if ok else "error"
        await websocket.send_json({"type": msg_type})
    except WebSocketDisconnect:
        logger.debug("WebSocket disconnected during build stream")
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


@org_router.delete("/{image_type}")
async def delete_sandbox_image(org_id: str, image_type: str):
    """Remove a sandbox image."""
    try:
        stype = SandboxType(image_type)
    except ValueError:
        raise HTTPException(404, f"Unknown sandbox type: {image_type}")

    ok = await sandbox_manager.provider.remove_image(stype)
    if not ok:
        raise HTTPException(500, f"Failed to remove image: {image_type}")

    # Reset in-memory build status
    status = get_build_status(stype)
    status.state = "idle"
    status.size_mb = None

    return {"status": "removed", "type": stype.value}

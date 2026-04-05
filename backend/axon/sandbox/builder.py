"""Sandbox image builder — async build with streaming progress."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel, Field

from axon.logging import get_logger
from axon.sandbox.types import (
    SANDBOX_PARENTS,
    SandboxType,
    get_ancestors,
    image_name,
)

logger = get_logger(__name__)

IMAGES_DIR = Path(__file__).parent / "images"


class BuildStatus(BaseModel):
    """Current state of a sandbox image build."""

    state: str = Field(default="idle", description="idle | building | ready | error")
    progress_lines: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    size_mb: float | None = None


# Module-level state
_build_status: dict[SandboxType, BuildStatus] = {}
_build_locks: dict[SandboxType, asyncio.Lock] = {}


def _get_lock(sandbox_type: SandboxType) -> asyncio.Lock:
    """Get or create a lock for the given sandbox type."""
    if sandbox_type not in _build_locks:
        _build_locks[sandbox_type] = asyncio.Lock()
    return _build_locks[sandbox_type]


def _get_status(sandbox_type: SandboxType) -> BuildStatus:
    """Get or create a build status for the given sandbox type."""
    if sandbox_type not in _build_status:
        _build_status[sandbox_type] = BuildStatus()
    return _build_status[sandbox_type]


def get_build_status(sandbox_type: SandboxType) -> BuildStatus:
    """Return current build status for a sandbox type."""
    return _get_status(sandbox_type)


def get_all_build_statuses() -> dict[str, BuildStatus]:
    """Return build statuses for all sandbox types."""
    return {t.value: _get_status(t) for t in SandboxType}


def _get_client() -> Any:
    """Get a Docker API client for streaming builds."""
    import docker
    return docker.APIClient()


async def image_exists(sandbox_type: SandboxType) -> bool:
    """Check if the Docker image for a sandbox type exists."""
    try:
        client = await asyncio.to_thread(_get_client)
        images = await asyncio.to_thread(client.images, name=image_name(sandbox_type))
        return len(images) > 0
    except Exception:
        return False


async def get_image_size(sandbox_type: SandboxType) -> float | None:
    """Return image size in MB, or None if image doesn't exist."""
    try:
        client = await asyncio.to_thread(_get_client)
        info = await asyncio.to_thread(client.inspect_image, image_name(sandbox_type))
        return round(info["Size"] / (1024 * 1024), 1)
    except Exception:
        return None


async def ensure_image(
    sandbox_type: SandboxType,
    on_progress: Callable[[str], None] | None = None,
) -> bool:
    """Ensure the image exists, building it if necessary."""
    if await image_exists(sandbox_type):
        status = _get_status(sandbox_type)
        status.state = "ready"
        status.size_mb = await get_image_size(sandbox_type)
        return True
    return await build_image(sandbox_type, on_progress)


async def build_image(
    sandbox_type: SandboxType,
    on_progress: Callable[[str], None] | None = None,
) -> bool:
    """Build a sandbox image, building parent images first."""
    lock = _get_lock(sandbox_type)
    async with lock:
        # Build ancestors first (root → leaf)
        for ancestor in get_ancestors(sandbox_type):
            if not await image_exists(ancestor):
                ok = await _run_build(ancestor, on_progress)
                if not ok:
                    return False

        return await _run_build(sandbox_type, on_progress)


async def _run_build(
    sandbox_type: SandboxType,
    on_progress: Callable[[str], None] | None = None,
) -> bool:
    """Execute a single image build in a thread."""
    status = _get_status(sandbox_type)
    status.state = "building"
    status.started_at = datetime.now(timezone.utc)
    status.progress_lines = []
    status.error = None

    dockerfile_dir = str(IMAGES_DIR / sandbox_type.value)
    ok = await asyncio.to_thread(
        _docker_build, sandbox_type, dockerfile_dir, status, on_progress,
    )

    if ok:
        status.state = "ready"
        status.size_mb = await get_image_size(sandbox_type)
    else:
        status.state = "error"

    status.completed_at = datetime.now(timezone.utc)
    return ok


async def remove_image(sandbox_type: SandboxType) -> bool:
    """Remove a sandbox image."""
    try:
        client = await asyncio.to_thread(_get_client)
        await asyncio.to_thread(client.remove_image, image_name(sandbox_type), force=True)
        status = _get_status(sandbox_type)
        status.state = "idle"
        status.size_mb = None
        logger.info("Removed image: %s", image_name(sandbox_type))
        return True
    except Exception as e:
        logger.warning("Failed to remove image %s: %s", image_name(sandbox_type), e)
        return False


def _docker_build(
    sandbox_type: SandboxType,
    dockerfile_dir: str,
    status: BuildStatus,
    on_progress: Callable[[str], None] | None,
) -> bool:
    """Synchronous Docker build with streaming (runs in thread)."""
    try:
        client = _get_client()
        tag = image_name(sandbox_type)
        stream = client.build(path=dockerfile_dir, tag=tag, rm=True, decode=True)

        for chunk in stream:
            line = chunk.get("stream", "").strip()
            if line:
                status.progress_lines.append(line)
                if on_progress:
                    on_progress(line)
            if "error" in chunk:
                err = chunk["error"].strip()
                status.error = err
                logger.error("Build error for %s: %s", sandbox_type.value, err)
                return False

        logger.info("Built image: %s", tag)
        return True
    except Exception as e:
        status.error = str(e)
        logger.error("Build failed for %s: %s", sandbox_type.value, e)
        return False

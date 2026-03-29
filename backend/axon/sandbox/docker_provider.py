"""Docker provider — runs sandboxes as local Docker containers."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable

from axon.sandbox.config import ImageSource, SandboxConfig
from axon.sandbox.containers import create_container
from axon.sandbox.provider import SandboxInstance
from axon.sandbox.types import SandboxType, image_name

logger = logging.getLogger(__name__)


class DockerProvider:
    """SandboxProvider implementation using the local Docker daemon."""

    def __init__(self, image_source: ImageSource = ImageSource.LOCAL) -> None:
        self._client: Any | None = None
        self._image_source = image_source

    def _get_client(self) -> Any:
        """Lazy-init high-level Docker client."""
        if self._client is None:
            import docker
            self._client = docker.from_env()
            self._client.ping()
            logger.info("Docker SDK connected")
        return self._client

    def _get_api_client(self) -> Any:
        """Low-level API client for streaming builds."""
        import docker
        return docker.APIClient()

    async def is_available(self) -> bool:
        try:
            await asyncio.to_thread(self._get_client)
            return True
        except Exception:
            return False

    # ── Image management ──────────────────────────────────────────

    async def ensure_image(
        self,
        sandbox_type: SandboxType,
        on_progress: Callable[[str], None] | None = None,
    ) -> bool:
        if await self.image_exists(sandbox_type):
            # Sync build status so the UI shows "ready"
            from axon.sandbox.builder import get_build_status
            status = get_build_status(sandbox_type)
            if status.state != "ready":
                status.state = "ready"
                status.size_mb = await self.get_image_size(sandbox_type)
            return True

        if self._image_source == ImageSource.REGISTRY:
            return await self._pull_image(sandbox_type, on_progress)
        return await self._build_image(sandbox_type, on_progress)

    async def _pull_image(
        self,
        sandbox_type: SandboxType,
        on_progress: Callable[[str], None] | None = None,
    ) -> bool:
        """Pull a pre-built image from the registry."""
        from axon.sandbox.builder import get_build_status
        from axon.config import settings

        registry = settings.sandbox_image_registry
        tag = image_name(sandbox_type, registry=registry)
        build_status = get_build_status(sandbox_type)
        build_status.state = "building"
        build_status.progress_lines = []

        if on_progress:
            on_progress(f"Pulling {tag}...")
        try:
            client = await asyncio.to_thread(self._get_api_client)
            stream = await asyncio.to_thread(
                client.pull, tag, stream=True, decode=True,
            )
            for chunk in stream:
                status = chunk.get("status", "")
                progress = chunk.get("progress", "")
                line = f"{status} {progress}".strip()
                if line:
                    build_status.progress_lines.append(line)
                    if on_progress:
                        on_progress(line)
            # Tag as local name so container creation works
            local_tag = image_name(sandbox_type)
            await asyncio.to_thread(client.tag, tag, local_tag)
            build_status.state = "ready"
            build_status.size_mb = await self.get_image_size(sandbox_type)
            if on_progress:
                on_progress(f"Image ready: {local_tag}")
            return True
        except Exception as e:
            build_status.state = "error"
            build_status.error = str(e)
            logger.error("Pull failed for %s: %s", sandbox_type.value, e)
            if on_progress:
                on_progress(f"Pull failed: {e}")
            return False

    async def _build_image(
        self,
        sandbox_type: SandboxType,
        on_progress: Callable[[str], None] | None = None,
    ) -> bool:
        """Build image from local Dockerfiles (dev mode)."""
        from axon.sandbox.builder import build_image
        return await build_image(sandbox_type, on_progress)

    async def image_exists(self, sandbox_type: SandboxType) -> bool:
        try:
            client = await asyncio.to_thread(self._get_api_client)
            tag = image_name(sandbox_type)
            images = await asyncio.to_thread(client.images, name=tag)
            return len(images) > 0
        except Exception:
            return False

    async def get_image_size(self, sandbox_type: SandboxType) -> float | None:
        try:
            client = await asyncio.to_thread(self._get_api_client)
            info = await asyncio.to_thread(client.inspect_image, image_name(sandbox_type))
            return round(info["Size"] / (1024 * 1024), 1)
        except Exception:
            return None

    async def remove_image(self, sandbox_type: SandboxType) -> bool:
        try:
            client = await asyncio.to_thread(self._get_api_client)
            await asyncio.to_thread(client.remove_image, image_name(sandbox_type), force=True)
            logger.info("Removed image: %s", image_name(sandbox_type))
            return True
        except Exception as e:
            logger.warning("Failed to remove image %s: %s", image_name(sandbox_type), e)
            return False

    # ── Container lifecycle ───────────────────────────────────────

    async def create_sandbox(
        self,
        org_id: str,
        agent_id: str,
        instance_id: str,
        runner_dir: str,
        workspace_dir: str,
        config: SandboxConfig,
        env: dict[str, str],
        init_script: str | None = None,
    ) -> str:
        container = await asyncio.to_thread(
            create_container, self._get_client(),
            org_id, agent_id, instance_id,
            runner_dir, workspace_dir, config, env,
            init_script=init_script,
        )
        return container.id

    async def stop_sandbox(self, sandbox_id: str, timeout: int = 10) -> None:
        c = self._get_client().containers.get(sandbox_id)
        await asyncio.to_thread(c.stop, timeout=timeout)

    async def destroy_sandbox(self, sandbox_id: str) -> None:
        c = self._get_client().containers.get(sandbox_id)
        await asyncio.to_thread(c.remove, force=True)

    async def get_status(self, sandbox_id: str) -> SandboxInstance | None:
        try:
            c = self._get_client().containers.get(sandbox_id)
            return SandboxInstance(
                sandbox_id=c.id,
                short_id=c.short_id,
                status=c.status,
                image=c.image.tags[0] if c.image.tags else "unknown",
                labels=c.labels,
            )
        except Exception:
            return None

    async def get_logs(self, sandbox_id: str, tail: int = 100) -> list[str]:
        try:
            c = self._get_client().containers.get(sandbox_id)
            raw = c.logs(tail=tail, timestamps=False).decode("utf-8", errors="replace")
            return raw.splitlines()
        except Exception:
            return []

    async def list_sandboxes(
        self, label_filter: dict[str, str] | None = None,
    ) -> list[SandboxInstance]:
        filters = {"label": [f"{k}={v}" for k, v in (label_filter or {}).items()]}
        containers = self._get_client().containers.list(filters=filters)
        return [
            SandboxInstance(
                sandbox_id=c.id, short_id=c.short_id,
                status=c.status,
                image=c.image.tags[0] if c.image.tags else "unknown",
                labels=c.labels,
            )
            for c in containers
        ]

    def backend_url(self) -> str:
        return "http://host.docker.internal:8000"

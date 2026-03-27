"""SandboxManager — create, start, stop, and destroy sandbox containers."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from axon.sandbox.config import SandboxConfig

logger = logging.getLogger(__name__)

# Container label for identifying Axon sandbox containers
LABEL_PREFIX = "axon.sandbox"


class SandboxManager:
    """Manages Docker sandbox containers for worker agents.

    Uses the Docker SDK (docker-py) to create isolated execution
    environments. Falls back gracefully if Docker is unavailable.
    """

    def __init__(self) -> None:
        self._client: Any | None = None
        self._containers: dict[str, str] = {}  # "org/agent" → container_id
        self._available: bool | None = None

    @property
    def client(self) -> Any:
        """Lazy-init Docker client."""
        if self._client is None:
            try:
                import docker
                self._client = docker.from_env()
                self._client.ping()
                self._available = True
                logger.info("Docker SDK connected")
            except Exception as e:
                self._available = False
                logger.warning("Docker not available: %s", e)
                raise RuntimeError("Docker is not available") from e
        return self._client

    @property
    def available(self) -> bool:
        """Check if Docker daemon is reachable."""
        if self._available is None:
            try:
                self.client  # triggers lazy init
            except RuntimeError:
                pass
        return self._available or False

    async def create(
        self,
        org_id: str,
        agent_id: str,
        runner_dir: str,
        workspace_dir: str,
        config: SandboxConfig,
        env: dict[str, str] | None = None,
    ) -> str:
        """Create and start a sandbox container.

        Returns the container ID.
        """
        key = f"{org_id}/{agent_id}"
        if key in self._containers:
            raise RuntimeError(f"Sandbox already exists: {key}")

        container = await asyncio.to_thread(
            self._create_container,
            key, runner_dir, workspace_dir, config, env or {},
        )

        self._containers[key] = container.id
        logger.info("Sandbox created: %s (id=%s)", key, container.short_id)
        return container.id

    def _create_container(
        self,
        key: str,
        runner_dir: str,
        workspace_dir: str,
        config: SandboxConfig,
        env: dict[str, str],
    ) -> Any:
        """Synchronous container creation (runs in thread)."""
        res = config.resources
        mounts = _build_mounts(runner_dir, workspace_dir, config.extra_mounts)

        labels = {
            f"{LABEL_PREFIX}.key": key,
            f"{LABEL_PREFIX}.managed": "true",
        }

        container = self.client.containers.create(
            image=config.image,
            name=f"axon-sandbox-{key.replace('/', '-')}",
            labels=labels,
            environment=env,
            volumes=mounts,
            nano_cpus=int(res.cpu_count * 1e9),
            mem_limit=f"{res.memory_mb}m",
            pids_limit=res.pids_limit,
            network_mode="bridge" if config.network.enabled else "none",
            auto_remove=config.auto_remove,
            detach=True,
        )
        container.start()
        return container

    async def stop(self, org_id: str, agent_id: str, timeout: int = 10) -> None:
        """Stop and remove a sandbox container."""
        key = f"{org_id}/{agent_id}"
        container_id = self._containers.pop(key, None)
        if not container_id:
            return

        try:
            container = self.client.containers.get(container_id)
            await asyncio.to_thread(container.stop, timeout=timeout)
            logger.info("Sandbox stopped: %s", key)
        except Exception as e:
            logger.warning("Failed to stop sandbox %s: %s", key, e)

    async def destroy(self, org_id: str, agent_id: str) -> None:
        """Force-remove a sandbox container."""
        key = f"{org_id}/{agent_id}"
        container_id = self._containers.pop(key, None)
        if not container_id:
            return

        try:
            container = self.client.containers.get(container_id)
            await asyncio.to_thread(container.remove, force=True)
            logger.info("Sandbox destroyed: %s", key)
        except Exception as e:
            logger.warning("Failed to destroy sandbox %s: %s", key, e)

    def status(self, org_id: str, agent_id: str) -> dict[str, Any]:
        """Get sandbox container status."""
        key = f"{org_id}/{agent_id}"
        container_id = self._containers.get(key)
        if not container_id:
            return {"running": False, "container_id": None}

        try:
            container = self.client.containers.get(container_id)
            return {
                "running": container.status == "running",
                "container_id": container.short_id,
                "status": container.status,
                "image": container.image.tags[0] if container.image.tags else "unknown",
            }
        except Exception:
            self._containers.pop(key, None)
            return {"running": False, "container_id": None}

    def logs(self, org_id: str, agent_id: str, tail: int = 100) -> list[str]:
        """Get recent container logs."""
        key = f"{org_id}/{agent_id}"
        container_id = self._containers.get(key)
        if not container_id:
            return []

        try:
            container = self.client.containers.get(container_id)
            raw = container.logs(tail=tail, timestamps=False).decode("utf-8", errors="replace")
            return raw.splitlines()
        except Exception:
            return []

    async def shutdown_all(self) -> None:
        """Stop all managed sandbox containers."""
        keys = list(self._containers.keys())
        for key in keys:
            org_id, agent_id = key.split("/", 1)
            await self.stop(org_id, agent_id)
        logger.info("All sandboxes shut down")


def _build_mounts(
    runner_dir: str,
    workspace_dir: str,
    extra: list[str],
) -> dict[str, dict[str, str]]:
    """Build Docker volume mount spec."""
    mounts: dict[str, dict[str, str]] = {
        runner_dir: {"bind": "/runner", "mode": "rw"},
        workspace_dir: {"bind": "/workspace", "mode": "rw"},
    }
    for mount_spec in extra:
        parts = mount_spec.split(":", 1)
        if len(parts) == 2:
            mounts[parts[0]] = {"bind": parts[1], "mode": "rw"}
    return mounts


# Singleton
sandbox_manager = SandboxManager()

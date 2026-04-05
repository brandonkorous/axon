"""SandboxManager — provider-agnostic sandbox orchestration.

Delegates all container/pod operations to a SandboxProvider (Docker or k8s).
"""

from __future__ import annotations

import uuid
from typing import Any

from axon.logging import get_logger
from axon.sandbox.config import (
    ImageSource,
    KubernetesConfig,
    SandboxConfig,
    SandboxProviderType,
)
from axon.sandbox.provider import SandboxProvider

logger = get_logger(__name__)


def create_provider(
    provider_type: SandboxProviderType = SandboxProviderType.DOCKER,
    image_source: ImageSource = ImageSource.LOCAL,
    k8s_config: KubernetesConfig | None = None,
) -> SandboxProvider:
    """Factory — instantiate the right provider based on config."""
    if provider_type == SandboxProviderType.KUBERNETES:
        from axon.sandbox.k8s_provider import KubernetesProvider
        return KubernetesProvider(k8s_config)
    from axon.sandbox.docker_provider import DockerProvider
    return DockerProvider(image_source)


class SandboxManager:
    """Manages sandbox lifecycle via a pluggable provider.

    Supports multiple parallel instances per agent via instance_id keying.
    """

    def __init__(self) -> None:
        self._provider: SandboxProvider | None = None
        self._containers: dict[str, str] = {}  # "org/agent/instance" -> sandbox_id

    @property
    def provider(self) -> SandboxProvider:
        """Lazy-init provider from settings."""
        if self._provider is None:
            self._provider = _provider_from_settings()
        return self._provider

    @property
    def available(self) -> bool:
        """Sync check — returns False until is_available() is called."""
        return self._provider is not None

    async def check_available(self) -> bool:
        """Async availability check against the runtime."""
        try:
            return await self.provider.is_available()
        except Exception:
            return False

    async def rediscover(self) -> int:
        """Re-populate _containers from running Docker containers with axon labels.

        Call on startup to recover tracking after a backend restart.
        """
        from axon.sandbox.containers import LABEL_PREFIX

        try:
            sandboxes = await self.provider.list_sandboxes(
                label_filter={f"{LABEL_PREFIX}.managed": "true"},
            )
        except Exception:
            return 0

        recovered = 0
        for sb in sandboxes:
            if sb.status != "running":
                continue
            key = sb.labels.get(f"{LABEL_PREFIX}.key", "")
            if key and key not in self._containers:
                self._containers[key] = sb.sandbox_id
                recovered += 1
                logger.info("Rediscovered sandbox: %s (id=%s)", key, sb.sandbox_id[:12])
        return recovered

    async def resolve_and_ensure(self, required_types: list[str]) -> str:
        """Resolve sandbox type from requirements and ensure the image exists."""
        from axon.sandbox.types import resolve_sandbox_type
        sandbox_type = resolve_sandbox_type(required_types)
        await self.provider.ensure_image(sandbox_type)
        return sandbox_type.value

    async def create(
        self,
        org_id: str,
        agent_id: str,
        runner_dir: str,
        workspace_dir: str,
        config: SandboxConfig,
        env: dict[str, str] | None = None,
        instance_id: str | None = None,
        git_repos: list[dict] | None = None,
        git_credentials: dict[str, dict] | None = None,
        plugin_mode: bool = False,
    ) -> str:
        """Create and start a sandbox. Returns the sandbox ID."""
        instance_id = instance_id or uuid.uuid4().hex[:8]
        key = f"{org_id}/{agent_id}/{instance_id}"
        if key in self._containers:
            # Destroy existing sandbox before recreating
            try:
                await self.provider.destroy_sandbox(self._containers[key])
            except Exception:
                pass
            del self._containers[key]

        # Ensure the image is available
        from axon.sandbox.types import SandboxType
        try:
            await self.provider.ensure_image(SandboxType(config.sandbox_type))
        except ValueError:
            logger.warning("Unknown sandbox type: %s, skipping ensure", config.sandbox_type)

        merged_env = dict(env or {})
        init_script: str | None = None

        if git_repos:
            from axon.sandbox.git_init import CLONE_SCRIPT, build_clone_env
            git_env = build_clone_env(git_repos, git_credentials or {})
            merged_env.update(git_env)
            init_script = CLONE_SCRIPT

        sandbox_id = await self.provider.create_sandbox(
            org_id, agent_id, instance_id,
            runner_dir, workspace_dir, config, merged_env,
            init_script=init_script,
            plugin_mode=plugin_mode,
        )
        self._containers[key] = sandbox_id
        logger.info("Sandbox created: %s (id=%s)", key, sandbox_id[:12])
        return sandbox_id

    def list_instances(self, org_id: str, agent_id: str) -> list[dict[str, Any]]:
        """List all running sandbox instances for an agent."""
        prefix = f"{org_id}/{agent_id}/"
        instances: list[dict[str, Any]] = []
        for key, sandbox_id in self._containers.items():
            if not key.startswith(prefix):
                continue
            iid = key.split("/", 2)[2]
            instances.append({
                "instance_id": iid,
                "sandbox_id": sandbox_id[:12],
                "status": "tracked",
            })
        return instances

    async def stop(
        self,
        org_id: str,
        agent_id: str,
        instance_id: str | None = None,
        timeout: int = 10,
    ) -> None:
        """Stop sandbox(es)."""
        for key in self._resolve_keys(org_id, agent_id, instance_id):
            sid = self._containers.pop(key, None)
            if not sid:
                continue
            try:
                await self.provider.stop_sandbox(sid, timeout=timeout)
                logger.info("Sandbox stopped: %s", key)
            except Exception as e:
                logger.warning("Failed to stop sandbox %s: %s", key, e)

    async def destroy(
        self,
        org_id: str,
        agent_id: str,
        instance_id: str | None = None,
    ) -> None:
        """Force-remove sandbox(es)."""
        for key in self._resolve_keys(org_id, agent_id, instance_id):
            sid = self._containers.pop(key, None)
            if not sid:
                continue
            try:
                await self.provider.destroy_sandbox(sid)
                logger.info("Sandbox destroyed: %s", key)
            except Exception as e:
                logger.warning("Failed to destroy sandbox %s: %s", key, e)

    def status(
        self,
        org_id: str,
        agent_id: str,
        instance_id: str | None = None,
    ) -> dict[str, Any]:
        """Get sandbox status (sync wrapper for route compat)."""
        keys = self._resolve_keys(org_id, agent_id, instance_id)
        if not keys:
            return {"running": False, "container_id": None}
        sid = self._containers.get(keys[0])
        if not sid:
            return {"running": False, "container_id": None}
        return {
            "running": True,
            "container_id": sid[:12],
            "instance_id": keys[0].split("/", 2)[2],
        }

    def logs(
        self,
        org_id: str,
        agent_id: str,
        instance_id: str | None = None,
        tail: int = 100,
    ) -> list[str]:
        """Get logs — sync stub; use async get_logs for full support."""
        return []

    async def get_logs_async(
        self,
        org_id: str,
        agent_id: str,
        instance_id: str | None = None,
        tail: int = 100,
    ) -> list[str]:
        """Get recent sandbox logs."""
        keys = self._resolve_keys(org_id, agent_id, instance_id)
        if not keys:
            return []
        sid = self._containers.get(keys[0])
        if not sid:
            return []
        return await self.provider.get_logs(sid, tail=tail)

    def _resolve_keys(
        self,
        org_id: str,
        agent_id: str,
        instance_id: str | None,
    ) -> list[str]:
        if instance_id:
            key = f"{org_id}/{agent_id}/{instance_id}"
            return [key] if key in self._containers else []
        prefix = f"{org_id}/{agent_id}/"
        return [k for k in self._containers if k.startswith(prefix)]

    async def shutdown_all(self) -> None:
        """Stop all managed sandboxes."""
        for key in list(self._containers.keys()):
            parts = key.split("/", 2)
            await self.stop(parts[0], parts[1], parts[2])
        logger.info("All sandboxes shut down")


def _provider_from_settings() -> SandboxProvider:
    """Read global settings and create the appropriate provider."""
    from axon.config import settings

    provider_type = SandboxProviderType(
        getattr(settings, "sandbox_provider", "docker"),
    )
    image_source = ImageSource(
        getattr(settings, "sandbox_image_source", "local"),
    )

    k8s_config = None
    if provider_type == SandboxProviderType.KUBERNETES:
        k8s_config = KubernetesConfig(
            namespace=getattr(settings, "sandbox_k8s_namespace", "axon-sandboxes"),
            image_registry=getattr(settings, "sandbox_image_registry", "ghcr.io/axon-ai"),
            kubeconfig_path=getattr(settings, "sandbox_k8s_kubeconfig", None) or None,
            storage_class=getattr(settings, "sandbox_k8s_storage_class", "standard"),
            service_account=getattr(settings, "sandbox_k8s_service_account", "axon-sandbox"),
        )

    return create_provider(provider_type, image_source, k8s_config)


# Singleton
sandbox_manager = SandboxManager()

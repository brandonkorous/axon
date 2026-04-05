"""Kubernetes provider — runs sandboxes as k8s pods with images from a registry."""

from __future__ import annotations

import asyncio
from typing import Any, Callable

from axon.logging import get_logger
from axon.sandbox.config import KubernetesConfig, SandboxConfig
from axon.sandbox.k8s_network import build_network_policy
from axon.sandbox.k8s_volumes import build_volumes_and_mounts
from axon.sandbox.provider import SandboxInstance
from axon.sandbox.types import SandboxType, image_name

logger = get_logger(__name__)

# Labels applied to every sandbox pod for identification and cleanup
LABEL_PREFIX = "axon.sandbox"

# Default runner command
_DEFAULT_CMD = ["bun", "run", "/runner/runner.js"]
_INIT_CMD = ["bash", "-c", "bash /runner/git_init.sh && exec bun run /runner/runner.js"]


class KubernetesProvider:
    """SandboxProvider implementation using Kubernetes pods."""

    def __init__(self, k8s_config: KubernetesConfig | None = None) -> None:
        self._config = k8s_config or KubernetesConfig()
        self._core: Any | None = None
        self._batch: Any | None = None
        self._networking: Any | None = None

    def _ensure_client(self) -> None:
        """Lazy-init k8s API clients."""
        if self._core is not None:
            return
        from kubernetes import client, config as k8s_config

        if self._config.kubeconfig_path:
            k8s_config.load_kube_config(config_file=self._config.kubeconfig_path)
        else:
            try:
                k8s_config.load_incluster_config()
            except k8s_config.ConfigException:
                k8s_config.load_kube_config()

        self._core = client.CoreV1Api()
        self._batch = client.BatchV1Api()
        self._networking = client.NetworkingV1Api()
        logger.info("Kubernetes client connected (namespace=%s)", self._config.namespace)

    async def is_available(self) -> bool:
        try:
            await asyncio.to_thread(self._ensure_client)
            await asyncio.to_thread(self._core.list_namespace, limit=1)
            return True
        except Exception:
            return False

    # ── Image management ──────────────────────────────────────────

    async def ensure_image(
        self,
        sandbox_type: SandboxType,
        on_progress: Callable[[str], None] | None = None,
    ) -> bool:
        """In k8s mode, images live in the registry. Pull is implicit on pod start."""
        tag = image_name(sandbox_type, registry=self._config.image_registry)
        if on_progress:
            on_progress(f"Image {tag} will be pulled on pod start")
        return True

    async def image_exists(self, sandbox_type: SandboxType) -> bool:
        """Registry images are assumed available. Pod pull will fail if not."""
        return True

    async def get_image_size(self, sandbox_type: SandboxType) -> float | None:
        """Size not available from registry without additional API calls."""
        return None

    async def remove_image(self, sandbox_type: SandboxType) -> bool:
        """Removing from registry is out of scope — managed via CI/CD."""
        logger.info("Image removal not applicable in k8s mode: %s", sandbox_type.value)
        return False

    # ── Pod lifecycle ─────────────────────────────────────────────

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
        self._ensure_client()
        pod_name = f"axon-sandbox-{org_id}-{agent_id}-{instance_id[:8]}"
        ns = self._config.namespace

        # Build volumes and mounts
        volumes, vol_mounts = build_volumes_and_mounts(
            org_id, agent_id, instance_id,
            runner_dir, workspace_dir, config.extra_mounts,
            storage_class=self._config.storage_class,
            init_script=init_script,
        )

        # Create ConfigMap for init script if needed
        if init_script:
            await self._create_init_configmap(
                f"git-init-{agent_id}-{instance_id[:8]}", ns, init_script,
            )

        pod_spec = self._build_pod_spec(
            pod_name, org_id, agent_id, instance_id,
            config, env, volumes, vol_mounts, init_script,
        )

        await asyncio.to_thread(
            self._core.create_namespaced_pod, namespace=ns, body=pod_spec,
        )

        # Apply network policy if needed
        net_policy = build_network_policy(pod_name, ns, config.network)
        if net_policy:
            await asyncio.to_thread(
                self._networking.create_namespaced_network_policy,
                namespace=ns, body=net_policy,
            )

        logger.info("K8s sandbox pod created: %s/%s", ns, pod_name)
        return pod_name

    async def stop_sandbox(self, sandbox_id: str, timeout: int = 10) -> None:
        self._ensure_client()
        ns = self._config.namespace
        try:
            await asyncio.to_thread(
                self._core.delete_namespaced_pod,
                name=sandbox_id, namespace=ns,
                grace_period_seconds=timeout,
            )
            logger.info("K8s sandbox stopped: %s", sandbox_id)
        except Exception as e:
            logger.warning("Failed to stop k8s sandbox %s: %s", sandbox_id, e)

    async def destroy_sandbox(self, sandbox_id: str) -> None:
        self._ensure_client()
        ns = self._config.namespace
        try:
            await asyncio.to_thread(
                self._core.delete_namespaced_pod,
                name=sandbox_id, namespace=ns,
                grace_period_seconds=0,
            )
            # Clean up associated NetworkPolicy
            await self._cleanup_network_policies(sandbox_id)
            logger.info("K8s sandbox destroyed: %s", sandbox_id)
        except Exception as e:
            logger.warning("Failed to destroy k8s sandbox %s: %s", sandbox_id, e)

    async def get_status(self, sandbox_id: str) -> SandboxInstance | None:
        self._ensure_client()
        try:
            pod = await asyncio.to_thread(
                self._core.read_namespaced_pod,
                name=sandbox_id, namespace=self._config.namespace,
            )
            return SandboxInstance(
                sandbox_id=pod.metadata.name,
                short_id=pod.metadata.name[-8:],
                status=pod.status.phase.lower() if pod.status.phase else "unknown",
                image=pod.spec.containers[0].image if pod.spec.containers else "unknown",
                instance_id=pod.metadata.labels.get(f"{LABEL_PREFIX}.instance", ""),
                labels=pod.metadata.labels or {},
            )
        except Exception:
            return None

    async def get_logs(self, sandbox_id: str, tail: int = 100) -> list[str]:
        self._ensure_client()
        try:
            raw = await asyncio.to_thread(
                self._core.read_namespaced_pod_log,
                name=sandbox_id, namespace=self._config.namespace,
                tail_lines=tail,
            )
            return raw.splitlines()
        except Exception:
            return []

    async def list_sandboxes(
        self, label_filter: dict[str, str] | None = None,
    ) -> list[SandboxInstance]:
        self._ensure_client()
        label_selector = ",".join(
            f"{k}={v}" for k, v in (label_filter or {}).items()
        )
        pods = await asyncio.to_thread(
            self._core.list_namespaced_pod,
            namespace=self._config.namespace,
            label_selector=label_selector or f"{LABEL_PREFIX}.managed=true",
        )
        return [
            SandboxInstance(
                sandbox_id=p.metadata.name,
                short_id=p.metadata.name[-8:],
                status=p.status.phase.lower() if p.status.phase else "unknown",
                image=p.spec.containers[0].image if p.spec.containers else "unknown",
                labels=p.metadata.labels or {},
            )
            for p in pods.items
        ]

    def backend_url(self) -> str:
        return "http://axon-backend.axon.svc.cluster.local:8000"

    # ── Internal helpers ──────────────────────────────────────────

    def _build_pod_spec(
        self,
        pod_name: str,
        org_id: str,
        agent_id: str,
        instance_id: str,
        config: SandboxConfig,
        env: dict[str, str],
        volumes: list[dict],
        vol_mounts: list[dict],
        init_script: str | None,
    ) -> dict:
        res = config.resources
        tag = image_name(
            SandboxType(config.sandbox_type),
            registry=self._config.image_registry,
        )
        labels = {
            f"{LABEL_PREFIX}.org": org_id,
            f"{LABEL_PREFIX}.agent": agent_id,
            f"{LABEL_PREFIX}.instance": instance_id,
            f"{LABEL_PREFIX}.managed": "true",
            f"{LABEL_PREFIX}.pod": pod_name,
        }
        command = _INIT_CMD if init_script else _DEFAULT_CMD

        return {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": pod_name, "namespace": self._config.namespace, "labels": labels},
            "spec": {
                "restartPolicy": "Never",
                "serviceAccountName": self._config.service_account,
                "containers": [{
                    "name": "sandbox",
                    "image": tag,
                    "command": command,
                    "env": [{"name": k, "value": v} for k, v in env.items()],
                    "volumeMounts": vol_mounts,
                    "resources": {
                        "requests": {"cpu": str(res.cpu_count), "memory": f"{res.memory_mb}Mi"},
                        "limits": {"cpu": str(res.cpu_count), "memory": f"{res.memory_mb}Mi"},
                    },
                }],
                "volumes": volumes,
            },
        }

    async def _create_init_configmap(self, name: str, namespace: str, script: str) -> None:
        body = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {"name": name, "namespace": namespace},
            "data": {"git_init.sh": script},
        }
        try:
            await asyncio.to_thread(
                self._core.create_namespaced_config_map, namespace=namespace, body=body,
            )
        except Exception:
            # May already exist from a previous run
            await asyncio.to_thread(
                self._core.replace_namespaced_config_map,
                name=name, namespace=namespace, body=body,
            )

    async def _cleanup_network_policies(self, pod_name: str) -> None:
        try:
            for suffix in ["-egress", "-deny-egress"]:
                try:
                    await asyncio.to_thread(
                        self._networking.delete_namespaced_network_policy,
                        name=f"{pod_name}{suffix}",
                        namespace=self._config.namespace,
                    )
                except Exception:
                    pass
        except Exception:
            pass

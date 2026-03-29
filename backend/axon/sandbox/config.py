"""Sandbox configuration — resource limits, network policies, mounts, provider selection."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, model_validator


class SandboxProviderType(str, Enum):
    """Container runtime provider."""

    DOCKER = "docker"
    KUBERNETES = "kubernetes"


class ImageSource(str, Enum):
    """Where sandbox images come from."""

    REGISTRY = "registry"  # Pull pre-built images (production default)
    LOCAL = "local"  # Build from local Dockerfiles (dev mode)


class KubernetesConfig(BaseModel):
    """Kubernetes-specific sandbox settings."""

    namespace: str = Field(default="axon-sandboxes", description="K8s namespace for sandbox pods")
    image_registry: str = Field(default="ghcr.io/brandonkorous/axon", description="Container image registry")
    kubeconfig_path: str | None = Field(default=None, description="Path to kubeconfig (None = in-cluster)")
    storage_class: str = Field(default="standard", description="StorageClass for PVCs")
    service_account: str = Field(default="axon-sandbox", description="ServiceAccount for pods")


class ResourceLimits(BaseModel):
    """Container resource constraints."""

    cpu_count: float = Field(default=2.0, description="CPU core limit")
    memory_mb: int = Field(default=2048, description="Memory limit in MB")
    disk_mb: int = Field(default=5120, description="Disk quota in MB")
    pids_limit: int = Field(default=256, description="Max number of processes")


class NetworkPolicy(BaseModel):
    """Network access restrictions for sandboxed containers."""

    enabled: bool = Field(default=True, description="Enable network access")
    allow_domains: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Allowed outbound domains (* = all)",
    )
    block_domains: list[str] = Field(
        default_factory=list,
        description="Blocked domains (overrides allow)",
    )
    allow_internal: bool = Field(
        default=True,
        description="Allow access to Axon backend API",
    )


class SandboxConfig(BaseModel):
    """Full sandbox configuration for a worker."""

    enabled: bool = Field(default=False, description="Run worker in sandbox")
    image: str = Field(default="axon-sandbox:latest", description="Docker image")
    sandbox_type: str = Field(default="base", description="Sandbox image type")
    resources: ResourceLimits = Field(default_factory=ResourceLimits)
    network: NetworkPolicy = Field(default_factory=NetworkPolicy)
    auto_remove: bool = Field(default=True, description="Remove container on stop")
    timeout_minutes: int = Field(default=60, description="Max container lifetime")
    extra_mounts: list[str] = Field(
        default_factory=list,
        description="Additional host:container mount paths",
    )

    @model_validator(mode="after")
    def _set_image_from_type(self):
        """Derive image name from sandbox_type when using default image."""
        if self.image == "axon-sandbox:latest":
            self.image = f"axon-sandbox-{self.sandbox_type}:latest"
        return self

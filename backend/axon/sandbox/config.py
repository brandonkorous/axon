"""Sandbox configuration — resource limits, network policies, mounts."""

from __future__ import annotations

from pydantic import BaseModel, Field


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
    resources: ResourceLimits = Field(default_factory=ResourceLimits)
    network: NetworkPolicy = Field(default_factory=NetworkPolicy)
    auto_remove: bool = Field(default=True, description="Remove container on stop")
    timeout_minutes: int = Field(default=60, description="Max container lifetime")
    extra_mounts: list[str] = Field(
        default_factory=list,
        description="Additional host:container mount paths",
    )

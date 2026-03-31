"""Sandbox provider protocol — abstract container runtime interface."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol, runtime_checkable

from axon.sandbox.config import SandboxConfig
from axon.sandbox.types import SandboxType


@dataclass
class SandboxInstance:
    """Standardized sandbox instance info returned by all providers."""

    sandbox_id: str  # container ID or pod name
    short_id: str  # display-friendly identifier
    status: str  # "running", "stopped", "pending", etc.
    image: str
    instance_id: str = ""
    labels: dict[str, str] = field(default_factory=dict)


@runtime_checkable
class SandboxProvider(Protocol):
    """Abstract container runtime provider.

    Implementations: DockerProvider (local), KubernetesProvider (cluster).
    """

    async def is_available(self) -> bool:
        """Check if the runtime is reachable."""
        ...

    # ── Image management ──────────────────────────────────────────

    async def ensure_image(
        self,
        sandbox_type: SandboxType,
        on_progress: Callable[[str], None] | None = None,
    ) -> bool:
        """Ensure the sandbox image is available (build or pull)."""
        ...

    async def image_exists(self, sandbox_type: SandboxType) -> bool:
        """Check if the sandbox image is available in the runtime."""
        ...

    async def get_image_size(self, sandbox_type: SandboxType) -> float | None:
        """Return image size in MB, or None if unavailable."""
        ...

    async def remove_image(self, sandbox_type: SandboxType) -> bool:
        """Remove a sandbox image from the runtime."""
        ...

    # ── Container / pod lifecycle ─────────────────────────────────

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
        plugin_mode: bool = False,
    ) -> str:
        """Create and start a sandbox. Returns a runtime-specific ID."""
        ...

    async def stop_sandbox(self, sandbox_id: str, timeout: int = 10) -> None:
        """Gracefully stop a sandbox."""
        ...

    async def destroy_sandbox(self, sandbox_id: str) -> None:
        """Force-remove a sandbox."""
        ...

    async def get_status(self, sandbox_id: str) -> SandboxInstance | None:
        """Get sandbox status, or None if not found."""
        ...

    async def get_logs(self, sandbox_id: str, tail: int = 100) -> list[str]:
        """Get recent log lines from a sandbox."""
        ...

    async def exec_command(
        self, sandbox_id: str, command: list[str], *, timeout: int = 120,
    ) -> tuple[int, str, str]:
        """Execute a command inside a running sandbox. Returns (exit_code, stdout, stderr)."""
        ...

    async def list_sandboxes(
        self, label_filter: dict[str, str] | None = None,
    ) -> list[SandboxInstance]:
        """List sandboxes matching optional label filters."""
        ...

    def backend_url(self) -> str:
        """Return the URL sandboxes should use to reach the Axon backend."""
        ...

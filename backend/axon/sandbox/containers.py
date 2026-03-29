"""Container creation helpers for SandboxManager."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from axon.sandbox.config import SandboxConfig
from axon.sandbox.mount_validation import validate_mount_spec

# Container label for identifying Axon sandbox containers
LABEL_PREFIX = "axon.sandbox"

# Default command when no init script is provided
_DEFAULT_CMD = ["bun", "run", "/runner/runner.js"]

# Command template when a git init script is present
_INIT_CMD = ["bash", "-c", "bash /runner/git_init.sh && exec bun run /runner/runner.js"]


def create_container(
    client: Any,
    org_id: str,
    agent_id: str,
    instance_id: str,
    runner_dir: str,
    workspace_dir: str,
    config: SandboxConfig,
    env: dict[str, str],
    init_script: str | None = None,
) -> Any:
    """Create and start a Docker container (synchronous, runs in thread)."""
    key = f"{org_id}/{agent_id}/{instance_id}"
    res = config.resources
    mounts = build_mounts(runner_dir, workspace_dir, config.extra_mounts)
    container_name = f"axon-sandbox-{org_id}-{agent_id}-{instance_id[:8]}"

    labels = {
        f"{LABEL_PREFIX}.key": key,
        f"{LABEL_PREFIX}.org": org_id,
        f"{LABEL_PREFIX}.agent": agent_id,
        f"{LABEL_PREFIX}.instance": instance_id,
        f"{LABEL_PREFIX}.managed": "true",
    }

    command = _DEFAULT_CMD
    if init_script:
        script_path = Path(runner_dir) / "git_init.sh"
        script_path.write_text(init_script, encoding="utf-8")
        command = _INIT_CMD

    container = client.containers.create(
        image=config.image,
        name=container_name,
        labels=labels,
        environment=env,
        volumes=mounts,
        command=command,
        nano_cpus=int(res.cpu_count * 1e9),
        mem_limit=f"{res.memory_mb}m",
        pids_limit=res.pids_limit,
        network_mode="bridge" if config.network.enabled else "none",
        auto_remove=config.auto_remove,
        detach=True,
    )
    container.start()
    return container


def build_mounts(
    runner_dir: str,
    workspace_dir: str,
    extra: list[str],
) -> dict[str, dict[str, str]]:
    """Build Docker volume mount spec."""
    mounts: dict[str, dict[str, str]] = {
        runner_dir: {"bind": "/runner", "mode": "rw"},
        workspace_dir: {"bind": "/workspace", "mode": "rw"},
    }
    from axon.config import settings

    axon_dirs = [settings.axon_orgs_dir]
    for mount_spec in extra:
        valid, error = validate_mount_spec(mount_spec, axon_dirs)
        if not valid:
            raise ValueError(f"Blocked mount: {error}")
        parts = mount_spec.split(":", 1)
        # Re-parse for Windows drive letter paths (C:\foo:/container)
        if len(parts) == 2 and len(parts[0]) == 1 and parts[0].isalpha():
            remainder = parts[1]
            colon_idx = remainder.find(":")
            if colon_idx > 0:
                host = parts[0] + ":" + remainder[:colon_idx]
                container = remainder[colon_idx + 1:]
                mounts[host] = {"bind": container, "mode": "rw"}
                continue
        if len(parts) == 2:
            mounts[parts[0]] = {"bind": parts[1], "mode": "rw"}
    return mounts

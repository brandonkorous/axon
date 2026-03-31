"""Sandbox plugin — containerized exec environment for agents."""

from __future__ import annotations

import base64
import json
import os
from typing import Any

from axon.plugins.base import BasePlugin
from axon.plugins.builtin.sandbox.tools import TOOL_SCHEMAS
from axon.plugins.manifest import PluginManifest

DEFAULT_IMAGE = "code"
WORKSPACE = "/workspace"


def _validate_path(file_path: str) -> str:
    """Resolve a relative path against /workspace and reject traversal."""
    normalized = os.path.normpath(os.path.join(WORKSPACE, file_path))
    if not normalized.startswith(WORKSPACE):
        raise ValueError(f"Path traversal blocked: {file_path}")
    return normalized


class SandboxPlugin(BasePlugin):
    """Containerized execution environment for agents."""

    manifest = PluginManifest(
        name="sandbox",
        version="1.0.0",
        description=(
            "Grants agent access to a containerized execution environment "
            "with a mounted directory and allowlisted executables."
        ),
        author="axon",
        tools=["sandbox_exec", "sandbox_read_file", "sandbox_write_file", "sandbox_list_dir"],
        auto_load=False,
        category="system",
        icon="box",
        sandbox_type="code",
    )

    def __init__(
        self,
        path: str = ".",
        executables: list[str] | None = None,
        image: str = DEFAULT_IMAGE,
        resources: dict[str, Any] | None = None,
        agent_id: str = "default",
        org_id: str = "default",
        instance_id: str = "",
        **kwargs: Any,
    ) -> None:
        super().__init__()
        # Store raw path — empty string means no host mount
        self._host_path = path if path and path != "." else ""
        self._executables = set(executables or [])
        self._image = image
        self._resources = resources or {}
        self._agent_id = agent_id
        self._org_id = org_id
        self._sandbox_id: str | None = None
        self._instance_id = instance_id or f"plugin-{agent_id}"

    def get_tools(self) -> list[dict[str, Any]]:
        return list(TOOL_SCHEMAS)

    async def _ensure_container(self) -> str:
        """Start the sandbox container via the manager if not running."""
        if self._sandbox_id:
            try:
                from axon.sandbox.manager import sandbox_manager
                status = sandbox_manager.status(self._org_id, self._agent_id, self._instance_id)
                if status.get("running"):
                    return self._sandbox_id
            except Exception:
                pass
            self._sandbox_id = None

        from axon.sandbox.config import ResourceLimits, SandboxConfig
        from axon.sandbox.manager import sandbox_manager

        resources = ResourceLimits(
            cpu_count=self._resources.get("cpu", 2.0),
            memory_mb=self._resources.get("memory_mb", 2048),
        )
        sandbox_type = self._image.replace("axon/", "").split(":")[0]
        config = SandboxConfig(
            sandbox_type=sandbox_type,
            image=f"axon-sandbox-{sandbox_type}:latest",
            resources=resources,
        )

        self._sandbox_id = await sandbox_manager.create(
            org_id=self._org_id,
            agent_id=self._agent_id,
            runner_dir="",
            workspace_dir=str(self._host_path),
            config=config,
            instance_id=self._instance_id,
            plugin_mode=True,
        )
        return self._sandbox_id

    async def on_unload(self) -> None:
        """Destroy the sandbox container via the manager."""
        await super().on_unload()
        if self._sandbox_id:
            try:
                from axon.sandbox.manager import sandbox_manager
                await sandbox_manager.destroy(
                    self._org_id, self._agent_id, self._instance_id,
                )
            except Exception:
                pass
            self._sandbox_id = None

    async def execute(self, tool_name: str, arguments: str) -> str:
        args: dict[str, Any] = json.loads(arguments) if arguments else {}
        handler = {
            "sandbox_exec": self._exec, "sandbox_read_file": self._read_file,
            "sandbox_write_file": self._write_file, "sandbox_list_dir": self._list_dir,
        }.get(tool_name)
        if handler is None:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
        try:
            return await handler(args)
        except Exception as exc:
            return json.dumps({"error": str(exc)})

    async def _exec(self, args: dict[str, Any]) -> str:
        command = args.get("command", "")
        cmd_args = args.get("args", [])

        if command not in self._executables:
            return json.dumps({
                "error": f"Command not allowed: {command}. Allowed: {sorted(self._executables)}",
            })

        cid = await self._ensure_container()
        from axon.sandbox.manager import sandbox_manager

        try:
            exit_code, stdout, stderr = await sandbox_manager.provider.exec_command(
                cid, [command, *cmd_args],
            )
            return json.dumps({"exit_code": exit_code, "stdout": stdout, "stderr": stderr})
        except Exception as e:
            return json.dumps({"error": f"Sandbox exec failed: {e}"})

    async def _read_file(self, args: dict[str, Any]) -> str:
        resolved = _validate_path(args.get("file_path", ""))
        cid = await self._ensure_container()
        from axon.sandbox.manager import sandbox_manager

        exit_code, stdout, _ = await sandbox_manager.provider.exec_command(
            cid, ["cat", resolved],
        )
        if exit_code != 0:
            return json.dumps({"error": f"Failed to read: {resolved}"})
        return json.dumps({"content": stdout, "size": len(stdout)})

    async def _write_file(self, args: dict[str, Any]) -> str:
        resolved = _validate_path(args.get("file_path", ""))
        content = args.get("content", "")
        cid = await self._ensure_container()
        from axon.sandbox.manager import sandbox_manager

        parent = os.path.dirname(resolved)
        if parent and parent != WORKSPACE:
            await sandbox_manager.provider.exec_command(cid, ["mkdir", "-p", parent])

        encoded = base64.b64encode(content.encode()).decode()
        exit_code, _, _ = await sandbox_manager.provider.exec_command(
            cid, ["bash", "-c", f"echo '{encoded}' | base64 -d > {resolved}"],
        )
        if exit_code != 0:
            return json.dumps({"error": f"Failed to write: {resolved}"})
        return json.dumps({"written": resolved, "size": len(content.encode())})

    async def _list_dir(self, args: dict[str, Any]) -> str:
        resolved = _validate_path(args.get("dir_path", "."))
        cid = await self._ensure_container()
        from axon.sandbox.manager import sandbox_manager

        exit_code, stdout, _ = await sandbox_manager.provider.exec_command(
            cid, ["ls", "-la", "--time-style=+%Y-%m-%d", resolved],
        )
        if exit_code != 0:
            return json.dumps({"error": f"Not a directory: {resolved}"})

        entries = [
            {"name": p[7], "type": "directory" if p[0].startswith("d") else "file",
             "size": int(p[4]) if p[4].isdigit() else 0}
            for line in stdout.strip().split("\n")[1:]  # Skip "total" line
            if len(p := line.split(None, 7)) >= 8 and p[7] not in (".", "..")
        ]
        return json.dumps({"entries": entries})

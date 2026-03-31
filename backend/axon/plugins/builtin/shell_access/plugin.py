"""Shell access plugin — host filesystem and executable access for agents."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import httpx

from axon.plugins.base import BasePlugin
from axon.plugins.manifest import PluginManifest

MAX_FILE_SIZE = 100 * 1024  # 100KB
EXEC_TIMEOUT = 120  # seconds


class ShellAccessPlugin(BasePlugin):
    """Scoped filesystem and executable access for agents."""

    manifest = PluginManifest(
        name="shell_access",
        version="1.0.0",
        description=(
            "Grants agent access to a specific directory and allowlisted "
            "executables on the host machine. HIGH TRUST."
        ),
        author="axon",
        tool_prefix="shell_",
        tools=["shell_exec", "shell_read_file", "shell_write_file", "shell_list_dir"],
        auto_load=False,
        triggers=[],
        category="system",
        icon="terminal",
    )

    def __init__(
        self,
        path: str = ".",
        executables: list[str] | None = None,
        agent_id: str = "default",
        instance_id: str = "",
        host_agent_id: str = "",
        host_agent_url: str = "",
        **kwargs: Any,
    ) -> None:
        super().__init__()
        self.path = Path(path).resolve()
        self.executables: list[str] = executables or []
        self._host_agent_id = host_agent_id
        self._host_agent_url = host_agent_url

    def configure(self, credentials: dict[str, Any] | None = None) -> None:
        """Accept path and executables from credentials dict."""
        super().configure(credentials)
        creds = credentials or {}
        if "path" in creds:
            self.path = Path(creds["path"]).resolve()
        if "executables" in creds:
            self.executables = list(creds["executables"])
        if "host_agent_url" in creds:
            self._host_agent_url = creds["host_agent_url"]
        if "host_agent_id" in creds:
            self._host_agent_id = creds["host_agent_id"]

    def _resolve_safe(self, relative: str) -> Path:
        """Resolve a relative path and verify it stays within the root."""
        resolved = (self.path / relative).resolve()
        if not resolved.is_relative_to(self.path):
            raise PermissionError(f"Path traversal blocked: {relative}")
        return resolved

    def get_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "shell_exec",
                    "description": (
                        "Execute an allowlisted executable in the configured directory. "
                        f"Allowed: {', '.join(self.executables) or '(none)'}."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "Executable name (must be allowlisted)"},
                            "args": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Command arguments",
                                "default": [],
                            },
                        },
                        "required": ["command"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "shell_read_file",
                    "description": "Read a file relative to the configured root directory.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Relative path to file"},
                        },
                        "required": ["file_path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "shell_write_file",
                    "description": "Write content to a file relative to the configured root directory.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Relative path to file"},
                            "content": {"type": "string", "description": "File content to write"},
                        },
                        "required": ["file_path", "content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "shell_list_dir",
                    "description": "List directory contents relative to the configured root directory.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "dir_path": {
                                "type": "string",
                                "description": "Relative directory path",
                                "default": ".",
                            },
                        },
                        "required": [],
                    },
                },
            },
        ]

    async def execute(self, tool_name: str, arguments: str) -> str:
        args = json.loads(arguments) if isinstance(arguments, str) else arguments
        try:
            if tool_name == "shell_exec":
                return await self._exec(args["command"], args.get("args", []))
            if tool_name == "shell_read_file":
                return await self._read_file(args["file_path"])
            if tool_name == "shell_write_file":
                return await self._write_file(args["file_path"], args["content"])
            if tool_name == "shell_list_dir":
                return await self._list_dir(args.get("dir_path", "."))
        except PermissionError as exc:
            return json.dumps({"error": str(exc)})
        except Exception as exc:
            return json.dumps({"error": f"{type(exc).__name__}: {exc}"})
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    # -- Proxy helpers -------------------------------------------------------

    async def _proxy_post(self, endpoint: str, payload: dict) -> str:
        """POST to host agent and return response text."""
        async with httpx.AsyncClient(timeout=EXEC_TIMEOUT) as client:
            resp = await client.post(
                f"{self._host_agent_url}{endpoint}", json=payload,
            )
            return resp.text

    async def _proxy_get(self, endpoint: str, params: dict) -> str:
        """GET from host agent and return response text."""
        async with httpx.AsyncClient(timeout=EXEC_TIMEOUT) as client:
            resp = await client.get(
                f"{self._host_agent_url}{endpoint}", params=params,
            )
            return resp.text

    # -- Tool implementations ------------------------------------------------

    async def _exec(self, command: str, args: list[str]) -> str:
        if self._host_agent_url:
            return await self._proxy_post("/exec", {
                "command": command, "args": args,
            })
        # Direct execution fallback (non-Docker)
        if command not in self.executables:
            return json.dumps({"error": f"Command not allowed: {command}. Allowed: {self.executables}"})
        try:
            proc = await asyncio.create_subprocess_exec(
                command,
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.path),
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=EXEC_TIMEOUT)
        except asyncio.TimeoutError:
            return json.dumps({"error": f"Command timed out after {EXEC_TIMEOUT}s"})
        except FileNotFoundError:
            return json.dumps({"error": f"Executable not found: {command}"})
        return json.dumps({
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
            "exit_code": proc.returncode,
        })

    async def _read_file(self, file_path: str) -> str:
        if self._host_agent_url:
            return await self._proxy_get("/read", {"path": file_path})
        # Direct fallback
        target = self._resolve_safe(file_path)
        if not target.is_file():
            return json.dumps({"error": f"Not a file: {file_path}"})
        size = target.stat().st_size
        if size > MAX_FILE_SIZE:
            return json.dumps({"error": f"File too large: {size} bytes (max {MAX_FILE_SIZE})"})
        content = target.read_text(encoding="utf-8", errors="replace")
        return json.dumps({"content": content, "size": size})

    async def _write_file(self, file_path: str, content: str) -> str:
        if self._host_agent_url:
            return await self._proxy_post("/write", {
                "path": file_path, "content": content,
            })
        # Direct fallback
        target = self._resolve_safe(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return json.dumps({"written": str(target), "size": len(content.encode("utf-8"))})

    async def _list_dir(self, dir_path: str) -> str:
        if self._host_agent_url:
            return await self._proxy_get("/list", {"path": dir_path})
        # Direct fallback
        target = self._resolve_safe(dir_path)
        if not target.is_dir():
            return json.dumps({"error": f"Not a directory: {dir_path}"})
        entries = []
        for entry in sorted(target.iterdir()):
            stat = entry.stat()
            entries.append({
                "name": entry.name,
                "type": "dir" if entry.is_dir() else "file",
                "size": stat.st_size,
            })
        return json.dumps({"path": str(target), "entries": entries})

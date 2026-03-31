"""Tool schemas for the sandbox plugin (OpenAI function-calling format)."""

from __future__ import annotations

from typing import Any

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "sandbox_exec",
            "description": "Execute an allowed command inside the sandboxed container.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Executable name (must be in allowlist)"},
                    "args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Arguments to pass to the command",
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
            "name": "sandbox_read_file",
            "description": "Read a file from the container workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path relative to /workspace"},
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sandbox_write_file",
            "description": "Write content to a file in the container workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path relative to /workspace"},
                    "content": {"type": "string", "description": "File content to write"},
                },
                "required": ["file_path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sandbox_list_dir",
            "description": "List files and directories in the container workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dir_path": {
                        "type": "string",
                        "description": "Path relative to /workspace",
                        "default": ".",
                    },
                },
            },
        },
    },
]

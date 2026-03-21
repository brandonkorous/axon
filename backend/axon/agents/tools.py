"""Tool definitions for agents — vault operations, delegation, agent recruitment."""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from axon.vault.vault import VaultManager


# ── Tool schemas (for LLM tool-use) ─────────────────────────────────

VAULT_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "vault_read",
            "description": "Read a file from the agent's memory vault. Returns the file content with frontmatter.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to the file (e.g., 'decisions/2026-03-20-pricing.md')",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "vault_write",
            "description": "Write or update a file in the agent's memory vault with YAML frontmatter.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path for the file (e.g., 'decisions/2026-03-20-new-decision.md')",
                    },
                    "name": {
                        "type": "string",
                        "description": "Descriptive name for the frontmatter",
                    },
                    "description": {
                        "type": "string",
                        "description": "One-line description (be specific — this helps find it later)",
                    },
                    "type": {
                        "type": "string",
                        "description": "Content type (e.g., 'decision', 'contact', 'hindsight')",
                    },
                    "tags": {
                        "type": "string",
                        "description": "Comma-separated tags",
                    },
                    "status": {
                        "type": "string",
                        "description": "Status: active, completed, archived, on-hold",
                        "default": "active",
                    },
                    "content": {
                        "type": "string",
                        "description": "The markdown content body",
                    },
                },
                "required": ["path", "name", "description", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "vault_search",
            "description": "Search across all vault files for a query. Returns matching files with snippets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (matches against titles, descriptions, tags, and content)",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "vault_list",
            "description": "List all files in a vault branch/directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "branch": {
                        "type": "string",
                        "description": "Branch name (e.g., 'decisions', 'contacts', 'hindsight')",
                    },
                },
                "required": ["branch"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "vault_backlinks",
            "description": "Find all files that link to a given file. Useful for understanding relationships.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path of the file to find backlinks for",
                    },
                },
                "required": ["path"],
            },
        },
    },
]

DELEGATION_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "delegate_task",
            "description": "Send a task to another agent for execution. The task will appear in their inbox.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to_agent": {
                        "type": "string",
                        "description": "ID of the agent to delegate to",
                    },
                    "task_description": {
                        "type": "string",
                        "description": "What needs to be done",
                    },
                    "context": {
                        "type": "string",
                        "description": "Why — what decision or goal this feeds into",
                    },
                    "expected_output": {
                        "type": "string",
                        "description": "What you want back (a report, code change, recommendation, etc.)",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "default": "medium",
                    },
                    "type": {
                        "type": "string",
                        "enum": ["research", "audit", "implement", "investigate"],
                        "default": "research",
                    },
                },
                "required": ["to_agent", "task_description", "context", "expected_output"],
            },
        },
    },
]

RECRUITMENT_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "request_agent",
            "description": "Request a new agent to be added to the team. The user will approve or deny.",
            "parameters": {
                "type": "object",
                "properties": {
                    "role": {
                        "type": "string",
                        "description": "The role/title for the new agent (e.g., 'Financial Analyst')",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Why this agent is needed",
                    },
                    "suggested_capabilities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Key capabilities the agent should have",
                    },
                },
                "required": ["role", "reason"],
            },
        },
    },
]


# ── Tool executors ───────────────────────────────────────────────────

class ToolExecutor:
    """Executes tool calls from agent responses."""

    def __init__(self, vault: VaultManager, agent_id: str):
        self.vault = vault
        self.agent_id = agent_id
        self._pending_recruitment: dict | None = None

    async def execute(self, tool_name: str, arguments: str) -> str:
        """Execute a tool call and return the result as a string."""
        try:
            args = json.loads(arguments)
        except json.JSONDecodeError:
            return f"Error: Invalid JSON arguments: {arguments}"

        handlers = {
            "vault_read": self._vault_read,
            "vault_write": self._vault_write,
            "vault_search": self._vault_search,
            "vault_list": self._vault_list,
            "vault_backlinks": self._vault_backlinks,
            "delegate_task": self._delegate_task,
            "request_agent": self._request_agent,
        }

        handler = handlers.get(tool_name)
        if not handler:
            return f"Error: Unknown tool: {tool_name}"

        try:
            return await handler(args)
        except Exception as e:
            return f"Error executing {tool_name}: {e}"

    async def _vault_read(self, args: dict) -> str:
        path = args["path"]
        try:
            content = self.vault.read_file_raw(path)
            return content
        except FileNotFoundError:
            return f"File not found: {path}"

    async def _vault_write(self, args: dict) -> str:
        path = args["path"]
        metadata = {
            "name": args.get("name", ""),
            "description": args.get("description", ""),
            "type": args.get("type", ""),
            "date": str(date.today()),
            "status": args.get("status", "active"),
            "tags": args.get("tags", ""),
        }
        content = args.get("content", "")
        self.vault.write_file(path, metadata, content)

        # Auto-update index
        parts = path.split("/")
        if len(parts) >= 2:
            branch = parts[0]
            name = parts[-1].removesuffix(".md")
            self.vault._update_branch_index(branch, name, metadata.get("description", ""))

        return f"Written: {path}"

    async def _vault_search(self, args: dict) -> str:
        results = self.vault.search(args["query"])
        if not results:
            return "No results found."
        lines = []
        for r in results[:10]:
            lines.append(f"- **{r['title']}** (`{r['path']}`): {r['snippet'][:150]}...")
        return "\n".join(lines)

    async def _vault_list(self, args: dict) -> str:
        files = self.vault.list_branch(args["branch"])
        if not files:
            return f"No files in branch: {args['branch']}"
        lines = [f"- [[{f['name']}]] — {f['description']}" for f in files]
        return "\n".join(lines)

    async def _vault_backlinks(self, args: dict) -> str:
        backlinks = self.vault.get_backlinks(args["path"])
        if not backlinks:
            return f"No files link to: {args['path']}"
        return "\n".join(f"- {bl}" for bl in backlinks)

    async def _delegate_task(self, args: dict) -> str:
        to_agent = args["to_agent"]
        today_str = str(date.today())
        slug = args.get("task_description", "task")[:40].lower().replace(" ", "-")
        task_path = f"inbox/{today_str}-{slug}.md"

        metadata = {
            "from": self.agent_id,
            "date": today_str,
            "priority": args.get("priority", "medium"),
            "status": "pending",
            "type": args.get("type", "research"),
        }
        content = (
            f"## Task\n{args['task_description']}\n\n"
            f"## Context\n{args['context']}\n\n"
            f"## Expected Output\n{args['expected_output']}"
        )

        # Write to the target agent's vault inbox
        # This will be resolved by the agent manager to the correct vault path
        self.vault.write_file(task_path, metadata, content)
        return f"Task delegated to {to_agent}: {task_path}"

    async def _request_agent(self, args: dict) -> str:
        # Store the request — it will be surfaced to the user via the API
        self._pending_recruitment = {
            "requested_by": self.agent_id,
            "role": args["role"],
            "reason": args["reason"],
            "suggested_capabilities": args.get("suggested_capabilities", []),
        }
        return (
            f"Agent recruitment request submitted: {args['role']}. "
            f"The user will be asked to approve or deny this request."
        )

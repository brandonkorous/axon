"""Tool definitions for agents — vault operations, delegation, agent recruitment."""

from __future__ import annotations

import json
from datetime import date, datetime
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

LEARNING_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "vault_link_outcome",
            "description": (
                "Link a known outcome to prior decisions or advice. "
                "Updates confidence on related entries based on whether "
                "the outcome was positive, negative, or mixed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "outcome_path": {
                        "type": "string",
                        "description": "Path to the outcome/result file in the vault",
                    },
                    "related_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Paths to decisions/advice that led to this outcome",
                    },
                    "outcome_type": {
                        "type": "string",
                        "enum": ["positive", "negative", "mixed"],
                        "description": "Whether the outcome validated or contradicted prior advice",
                    },
                },
                "required": ["outcome_path", "related_paths", "outcome_type"],
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

    def __init__(
        self,
        vault: VaultManager,
        agent_id: str,
        shared_vault: "VaultManager | None" = None,
        audit_logger: "AuditLogger | None" = None,
        org_id: str = "",
        memory_manager: "MemoryManager | None" = None,
        reasoning_engine: "ReasoningEngine | None" = None,
        conversation_manager: "Any | None" = None,
        ws_target: str = "",
        advisor_ids: list[str] | None = None,
        comms_executor: "CommsToolExecutor | None" = None,
        web_executor: "WebToolExecutor | None" = None,
    ):
        self.vault = vault
        self.agent_id = agent_id
        self.org_id = org_id
        self.conversation_manager = conversation_manager
        self._pending_recruitment: dict | None = None
        self._audit_logger: "AuditLogger | None" = audit_logger
        self._memory_manager = memory_manager

        # Reasoning engine executor
        self._reasoning_executor: "ReasoningToolExecutor | None" = None
        if reasoning_engine:
            from axon.reasoning.tools import ReasoningToolExecutor
            self._reasoning_executor = ReasoningToolExecutor(reasoning_engine)

        # Comms executor for email/discord/contact tools
        self._comms_executor: "CommsToolExecutor | None" = comms_executor

        # Web executor for search/fetch tools
        self._web_executor: "WebToolExecutor | None" = web_executor

        # Shared vault executor for task/issue/knowledge tools
        self._shared_executor: "SharedVaultToolExecutor | None" = None
        if shared_vault:
            from axon.agents.shared_tools import SharedVaultToolExecutor
            self._shared_executor = SharedVaultToolExecutor(
                shared_vault, agent_id,
                conversation_manager=conversation_manager,
                ws_target=ws_target,
                org_id=org_id,
                advisor_ids=advisor_ids or [],
            )

    _SHARED_TOOL_PREFIXES = ("task_", "issue_", "achievement_", "knowledge_")

    async def execute(self, tool_name: str, arguments: str) -> str:
        """Execute a tool call and return the result as a string."""
        # Route reasoning tools to the reasoning executor
        if self._reasoning_executor and tool_name.startswith("reason_"):
            result = await self._reasoning_executor.execute(tool_name, arguments)
            self._log_audit(tool_name, arguments, result)
            return result

        # Route comms tools to the comms executor
        if self._comms_executor and tool_name.startswith("comms_"):
            result = await self._comms_executor.execute(tool_name, arguments)
            self._log_audit(tool_name, arguments, result)
            return result

        # Route web tools to the web executor
        if self._web_executor and tool_name.startswith("web_"):
            result = await self._web_executor.execute(tool_name, arguments)
            self._log_audit(tool_name, arguments, result)
            return result

        # Route shared vault tools to the shared executor
        if self._shared_executor and tool_name.startswith(self._SHARED_TOOL_PREFIXES):
            result = await self._shared_executor.execute(tool_name, arguments)
            self._log_audit(tool_name, arguments, result)
            return result

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
            "vault_link_outcome": self._vault_link_outcome,
            "delegate_task": self._delegate_task,
            "request_agent": self._request_agent,
        }

        handler = handlers.get(tool_name)
        if not handler:
            return f"Error: Unknown tool: {tool_name}"

        try:
            result = await handler(args)
            self._log_audit(tool_name, arguments, result)
            return result
        except Exception as e:
            error_result = f"Error executing {tool_name}: {e}"
            self._log_audit(tool_name, arguments, error_result)
            return error_result

    def _log_audit(self, tool_name: str, arguments: str, result: str) -> None:
        """Log a tool execution to the audit trail."""
        if not self._audit_logger:
            return
        try:
            self._audit_logger.log(
                agent_id=self.agent_id,
                action=tool_name,
                tool=tool_name,
                conversation_id=self.agent_id,
                org_id=self.org_id,
                arguments=arguments,
                result_summary=result[:500],
            )
        except Exception:
            pass  # Never let audit failure break tool execution

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

    async def _vault_link_outcome(self, args: dict) -> str:
        if not self._memory_manager:
            return "Error: Learning engine is not enabled for this agent."
        return await self._memory_manager.link_outcome(
            outcome_path=args["outcome_path"],
            related_paths=args["related_paths"],
            outcome_type=args["outcome_type"],
        )

    async def _delegate_task(self, args: dict) -> str:
        import axon.registry as registry

        to_agent = args["to_agent"]

        # Resolve the target agent's vault
        target = registry.get_agent(self.org_id, to_agent)
        if not target:
            target = registry.agent_registry.get(to_agent)
        if not target:
            return f"Error: Agent '{to_agent}' not found."

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

        # Write to the TARGET agent's vault inbox (not our own)
        target.vault.write_file(task_path, metadata, content)

        # Also create a trackable shared vault task for scheduler pickup
        if self._shared_executor:
            from axon.agents.shared_tools import _slugify
            shared_slug = _slugify(args["task_description"][:80])
            shared_path = f"tasks/{today_str}-{shared_slug}.md"
            priority_map = {"high": "p1", "medium": "p2", "low": "p3"}
            conv_id = (
                self.conversation_manager.active_id
                if hasattr(self, "conversation_manager") and self.conversation_manager
                else ""
            )
            shared_meta = {
                "name": args["task_description"][:80],
                "type": "task",
                "assignee": to_agent,
                "status": "in_progress",
                "priority": priority_map.get(args.get("priority", "medium"), "p2"),
                "delegation_ref": task_path,
                "created_by": self.agent_id,
                "conversation_id": conv_id,
                "ws_target": self.agent_id,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.utcnow().isoformat() + "Z",
            }
            shared_content = (
                f"# {args['task_description'][:80]}\n\n{content}"
            )
            self._shared_executor.vault.write_file(
                shared_path, shared_meta, shared_content,
            )

        return f"Task delegated to {to_agent}: {task_path}"

    async def _request_agent(self, args: dict) -> str:
        # Store in-memory for the current response
        self._pending_recruitment = {
            "requested_by": self.agent_id,
            "role": args["role"],
            "reason": args["reason"],
            "suggested_capabilities": args.get("suggested_capabilities", []),
        }

        # Persist to shared vault so it survives restarts and is visible to the API
        if self._shared_executor:
            from axon.agents.shared_tools import _slugify
            today_str = str(date.today())
            slug = _slugify(args["role"][:60])
            task_path = f"tasks/{today_str}-recruit-{slug}.md"
            capabilities = ", ".join(args.get("suggested_capabilities", []))
            meta = {
                "name": f"Recruit: {args['role']}",
                "type": "recruitment",
                "status": "awaiting_approval",
                "priority": "p2",
                "requested_by": self.agent_id,
                "role": args["role"],
                "reason": args["reason"],
                "suggested_capabilities": args.get("suggested_capabilities", []),
                "created_at": datetime.utcnow().isoformat() + "Z",
            }
            body = (
                f"# Recruitment Request: {args['role']}\n\n"
                f"**Requested by:** {self.agent_id}\n"
                f"**Reason:** {args['reason']}\n"
            )
            if capabilities:
                body += f"**Capabilities:** {capabilities}\n"
            self._shared_executor.vault.write_file(task_path, meta, body)

        return (
            f"Agent recruitment request submitted: {args['role']}. "
            f"The user will be asked to approve or deny this request."
        )

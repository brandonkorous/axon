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
                    "mode": {
                        "type": "string",
                        "enum": ["async", "sync"],
                        "description": (
                            "async (default): fire-and-forget — task goes to inbox, "
                            "results arrive later. sync: wait for the agent to complete "
                            "and return the result inline."
                        ),
                        "default": "async",
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
            "description": (
                "Request a new agent to be added to the team. The user will approve or deny. "
                "Describe what you need — the system will automatically craft a detailed "
                "persona and instructions for the new agent based on your brief."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "role": {
                        "type": "string",
                        "description": "The role/title for the new agent (e.g., 'Design Lead')",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Why this agent is needed",
                    },
                    "description": {
                        "type": "string",
                        "description": (
                            "Describe what this agent should do — their focus areas, "
                            "what kind of work they'll handle, and who they should "
                            "coordinate with. Be as specific as you can about the need."
                        ),
                    },
                },
                "required": ["role", "reason", "description"],
            },
        },
    },
]


PIPELINE_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "pipeline_run",
            "description": "Run a named pipeline workflow. Pipelines chain multiple agents sequentially or in parallel, where each agent's output feeds the next.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pipeline_name": {
                        "type": "string",
                        "description": "Name of the pipeline to execute (e.g. 'feature_review', 'strategic_decision')",
                    },
                    "message": {
                        "type": "string",
                        "description": "The input message or question to run through the pipeline",
                    },
                },
                "required": ["pipeline_name", "message"],
            },
        },
    },
]


DISCOVERY_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "find_agents",
            "description": (
                "Search the organization's agent registry. Returns agents matching "
                "the given filters. Use this to discover agents beyond your immediate "
                "team — e.g., workers, sub-agents, or specialists deeper in the org."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Free-text search across agent names, titles, and taglines",
                    },
                    "type": {
                        "type": "string",
                        "enum": ["advisor", "external"],
                        "description": "Filter by agent type",
                    },
                    "parent_id": {
                        "type": "string",
                        "description": "Filter by parent agent ID (find children of a specific agent)",
                    },
                    "delegatable": {
                        "type": "boolean",
                        "description": "If true, only return agents you are allowed to delegate work to",
                    },
                },
                "required": [],
            },
        },
    },
]

PERFORMANCE_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "perf_get_metrics",
            "description": "Get your own performance metrics for the current or specified period. Shows recommendations made, adoption rate, outcomes, and confidence.",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": "Time period (e.g. '2026-W13' for week 13, or empty for current week)",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "perf_run_retro",
            "description": "Generate a retrospective analysis of your own performance — insights, areas for improvement, and trend data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": "Time period to analyze (empty for current week)",
                    },
                },
                "required": [],
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
        browser_executor: "BrowserToolExecutor | None" = None,
        media_executor: "MediaToolExecutor | None" = None,
        integration_executor: "IntegrationToolExecutor | None" = None,
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

        # Browser executor for Playwright-based automation
        self._browser_executor: "BrowserToolExecutor | None" = browser_executor

        # Media executor for YouTube/podcast consumption
        self._media_executor: "MediaToolExecutor | None" = media_executor

        # Integration executor for external service plugins
        self._integration_executor: "IntegrationToolExecutor | None" = integration_executor

        # Stream callback — allows tools to emit StreamChunks mid-execution
        self._stream_callback: Any = None  # set by Agent after init

        # Research executor for structured research workflows
        from axon.research.executor import ResearchToolExecutor
        self._research_executor = ResearchToolExecutor()

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

        # Performance tracker for perf_* tools
        self._perf_tracker: "PerformanceTracker | None" = None
        if shared_vault:
            from axon.performance.tracker import PerformanceTracker
            self._perf_tracker = PerformanceTracker(shared_vault)

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

        # Route research tools to the research executor
        if tool_name.startswith("research_"):
            result = await self._research_executor.execute(tool_name, arguments, self.agent_id)
            self._log_audit(tool_name, arguments, result)
            return result

        # Route browser tools to the browser executor
        if self._browser_executor and tool_name.startswith("browser_"):
            result = await self._browser_executor.execute(tool_name, arguments, self.agent_id)
            self._log_audit(tool_name, arguments, result)
            return result

        # Route media tools to the media executor
        if self._media_executor and tool_name.startswith("media_"):
            result = await self._media_executor.execute(tool_name, arguments)
            self._log_audit(tool_name, arguments, result)
            return result

        # Route integration tools to the integration executor
        if self._integration_executor and tool_name in self._integration_executor._handler_map:
            result = await self._integration_executor.execute(tool_name, arguments)
            self._log_audit(tool_name, arguments, result)
            return result

        # Route shared vault tools to the shared executor
        if self._shared_executor and tool_name.startswith(self._SHARED_TOOL_PREFIXES):
            result = await self._shared_executor.execute(tool_name, arguments)
            self._log_audit(tool_name, arguments, result)
            return result

        # Route performance tools to the performance tracker
        if self._perf_tracker and tool_name.startswith("perf_"):
            result = await self._execute_perf_tool(tool_name, arguments)
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
            "find_agents": self._find_agents,
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
        from axon.agents.agent import StreamChunk

        to_agent = args["to_agent"]
        mode = args.get("mode", "async")

        # Resolve the target agent
        target = registry.get_agent(self.org_id, to_agent)
        if not target:
            target = registry.agent_registry.get(to_agent)
        if not target:
            return f"Error: Agent '{to_agent}' not found."

        task_desc = args["task_description"]

        # Emit activation event (both modes)
        await self._emit_stream_event(StreamChunk(
            agent_id=self.agent_id,
            type="agent_activated",
            content=f"Delegating to {to_agent}...",
            metadata={
                "target_agent": to_agent,
                "target_name": getattr(target, "name", to_agent),
                "task_description": task_desc[:200],
                "mode": mode,
            },
        ))

        # ── Sync mode: execute directly and return result inline ──
        if mode == "sync":
            # Fail fast if target is busy
            if hasattr(target, "_processing_lock") and target._processing_lock.locked():
                return await self._delegate_task_async(args, target, to_agent)

            prompt = (
                f"[DELEGATED TASK from {self.agent_id}]\n\n"
                f"## Task\n{task_desc}\n\n"
                f"## Context\n{args['context']}\n\n"
                f"## Expected Output\n{args['expected_output']}"
            )

            result_text = ""
            try:
                async for chunk in target.process(prompt, save_history=False):
                    if chunk.type == "text":
                        result_text += chunk.content
            except Exception as e:
                logger.error("[delegate_task] Sync delegation to %s failed: %s", to_agent, e)
                await self._emit_stream_event(StreamChunk(
                    agent_id=self.agent_id,
                    type="agent_result",
                    content="",
                    metadata={
                        "source_agent": to_agent,
                        "task_summary": task_desc[:200],
                        "status": "failed",
                        "error": str(e),
                    },
                ))
                return f"Error: Sync delegation to {to_agent} failed: {e}"

            await self._emit_stream_event(StreamChunk(
                agent_id=self.agent_id,
                type="agent_result",
                content=result_text[:500],
                metadata={
                    "source_agent": to_agent,
                    "source_name": getattr(target, "name", to_agent),
                    "task_summary": task_desc[:200],
                    "status": "success",
                },
            ))

            return f"[Result from {to_agent}]:\n\n{result_text}"

        # ── Async mode (default): write to inbox + shared vault ──
        return await self._delegate_task_async(args, target, to_agent)

    async def _delegate_task_async(self, args: dict, target: Any, to_agent: str) -> str:
        """Async delegation — write task to inbox for scheduler pickup."""
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
            # External agents (workers) pick up "pending" tasks via REST polling;
            # regular agents pick up "in_progress" tasks via the scheduler.
            is_target_external = getattr(target, "is_external", False)
            task_status = "pending" if is_target_external else "in_progress"
            shared_meta = {
                "name": args["task_description"][:80],
                "type": "task",
                "assignee": to_agent,
                "status": task_status,
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

        return f"Task delegated to {to_agent} (async): {task_path}"

    async def _emit_stream_event(self, chunk: Any) -> None:
        """Emit a stream event via the callback (set by Agent)."""
        if self._stream_callback:
            await self._stream_callback(chunk)

    async def _request_agent(self, args: dict) -> str:
        import asyncio as _asyncio
        import logging as _logging
        _log = _logging.getLogger(__name__)

        role = args["role"]
        reason = args["reason"]
        description = args.get("description", "")
        _log.info("[RECRUIT] %s requesting '%s'", self.agent_id, role)

        # Write the request to the vault immediately with pending refinement
        task_path = ""
        if self._shared_executor:
            from axon.agents.shared_tools import _slugify
            today_str = str(date.today())
            slug = _slugify(role[:60])
            task_path = f"tasks/{today_str}-recruit-{slug}.md"
            meta = {
                "name": f"Recruit: {role}",
                "type": "recruitment",
                "status": "refining",
                "priority": "p2",
                "requested_by": self.agent_id,
                "role": role,
                "reason": reason,
                "system_prompt": "",
                "domains": [],
                "description": description,
                "suggested_capabilities": [],
                "created_at": datetime.utcnow().isoformat() + "Z",
            }
            body = (
                f"# Recruitment Request: {role}\n\n"
                f"**Requested by:** {self.agent_id}\n"
                f"**Reason:** {reason}\n"
                f"**Description:** {description}\n\n"
                f"*Prompt refinement in progress...*\n"
            )
            self._shared_executor.vault.write_file(task_path, meta, body)
            _log.info("[RECRUIT] Written draft to %s — refinement starting in background", task_path)

        # Store in-memory for the current response
        self._pending_recruitment = {
            "requested_by": self.agent_id,
            "role": role,
            "reason": reason,
        }

        # Fire off refinement in the background — don't block the response
        _asyncio.create_task(self._refine_and_update_recruitment(
            role=role,
            reason=reason,
            description=description,
            task_path=task_path,
        ))

        return (
            f"Recruitment request submitted for '{role}'. "
            f"The system is crafting a detailed persona in the background — "
            f"it will appear in the approval queue once ready."
        )

    async def _refine_and_update_recruitment(
        self,
        role: str,
        reason: str,
        description: str,
        task_path: str,
    ) -> None:
        """Background task: refine a recruitment brief and update the vault entry."""
        import logging as _logging
        _log = _logging.getLogger(__name__)

        try:
            # Build team roster context
            roster_lines = []
            if self.org_id:
                import axon.registry as _reg
                org = _reg.get_org(self.org_id)
                if org:
                    for aid, agent in org.agent_registry.items():
                        if hasattr(agent, "config"):
                            cfg = agent.config
                            domains = cfg.guardrails.domains.allowed_domains if cfg.guardrails.has_domain_boundaries else []
                            domain_str = f" — domains: {', '.join(domains)}" if domains else ""
                            roster_lines.append(f"- {cfg.name} (`{aid}`): {cfg.title}{domain_str}")
            roster_context = "\n".join(roster_lines) if roster_lines else "No existing agents."

            # Refine via LLM
            _log.info("[RECRUIT] Refining prompt for '%s'...", role)
            system_prompt, domains = await self._refine_recruitment_prompt(
                role=role,
                reason=reason,
                description=description,
                requested_by=self.agent_id,
                team_roster=roster_context,
            )
            _log.info("[RECRUIT] Refinement complete for '%s' — %d domains, %d chars",
                       role, len(domains), len(system_prompt))

            # Update the vault entry with the refined prompt
            if task_path and self._shared_executor:
                meta, _body = self._shared_executor.vault.read_file(task_path)
                meta["system_prompt"] = system_prompt
                meta["domains"] = domains
                meta["status"] = "awaiting_approval"
                domain_str = ", ".join(domains)
                body = (
                    f"# Recruitment Request: {role}\n\n"
                    f"**Requested by:** {self.agent_id}\n"
                    f"**Reason:** {reason}\n"
                )
                if domain_str:
                    body += f"**Domains:** {domain_str}\n"
                body += f"\n## System Prompt\n\n{system_prompt}\n"
                self._shared_executor.vault.write_file(task_path, meta, body)
                _log.info("[RECRUIT] Updated %s → awaiting_approval", task_path)

        except Exception:
            _log.exception("[RECRUIT] Background refinement failed for '%s'", role)
            # Still flip to awaiting_approval with the raw description as fallback
            if task_path and self._shared_executor:
                try:
                    meta, _body = self._shared_executor.vault.read_file(task_path)
                    meta["system_prompt"] = description
                    meta["status"] = "awaiting_approval"
                    self._shared_executor.vault.write_file(task_path, meta, _body)
                    _log.info("[RECRUIT] Fallback: promoted %s with raw description", task_path)
                except Exception:
                    _log.exception("[RECRUIT] Fallback write also failed for %s", task_path)

    async def _refine_recruitment_prompt(
        self,
        role: str,
        reason: str,
        description: str,
        requested_by: str,
        team_roster: str,
    ) -> tuple[str, list[str]]:
        """Use an LLM to refine a recruitment brief into a full agent persona."""
        from axon.agents.provider import complete
        from axon.config import settings
        import json as _json

        refinement_system = (
            "You are an agent architect. Your job is to take a rough hiring brief and "
            "produce a polished, detailed agent persona.\n\n"
            "You will receive:\n"
            "- The requested role and why it's needed\n"
            "- A brief description from the requesting agent\n"
            "- The current team roster (so you know who exists and can reference them)\n\n"
            "Produce a JSON object with exactly two keys:\n"
            '- "system_prompt": A well-structured persona prompt (string) that includes:\n'
            "  1. A clear identity statement — who they are and their role\n"
            "  2. Core responsibilities (5-8 bullet points, specific to the role)\n"
            "  3. How they operate — principles, approach, what makes them effective\n"
            "  4. Coordination points — which existing team members they work with and on what\n"
            "  Write it in second person (\"You are...\"). Be specific, not generic. "
            "  A Design Lead needs different instructions than a Data Analyst. "
            "  Do NOT include instructions about vault usage, tool usage, or team building — "
            "  those are injected automatically by the system.\n"
            '- "domains": An array of 3-6 advisory domain strings that define this agent\'s '
            "  area of expertise (e.g., [\"UI/UX design\", \"design systems\", \"visual branding\"])\n\n"
            "Return ONLY the JSON object, no markdown fencing or extra text."
        )

        user_message = (
            f"## Hiring Brief\n\n"
            f"**Role:** {role}\n"
            f"**Reason:** {reason}\n"
            f"**Description:** {description}\n"
            f"**Requested by:** {requested_by}\n\n"
            f"## Current Team\n\n{team_roster}"
        )

        try:
            import asyncio as _asyncio
            response = await _asyncio.wait_for(
                complete(
                    model=settings.default_model,
                    messages=[
                        {"role": "system", "content": refinement_system},
                        {"role": "user", "content": user_message},
                    ],
                    max_tokens=2048,
                    temperature=0.7,
                ),
                timeout=15,
            )
            content = response.get("content", "")
            # Strip markdown code fencing if present
            if "```" in content:
                # Handle ```json ... ``` or ``` ... ```
                import re
                json_match = re.search(r"```(?:json)?\s*\n?(.*?)```", content, re.DOTALL)
                if json_match:
                    content = json_match.group(1).strip()
            parsed = _json.loads(content)
            return parsed.get("system_prompt", description), parsed.get("domains", [])
        except Exception as e:
            # Fallback: use the raw description if refinement fails
            import logging
            logging.getLogger(__name__).warning("Recruitment prompt refinement failed: %s", e)
            return description, []

    async def _find_agents(self, args: dict) -> str:
        """Search the org agent registry with optional filters."""
        import axon.registry as registry

        org = registry.get_org(self.org_id)
        if not org:
            return "Error: Organization not found."

        query = args.get("query", "").lower()
        type_filter = args.get("type", "")
        parent_filter = args.get("parent_id", "")
        delegatable = args.get("delegatable", False)

        # Resolve caller's delegation list
        caller_delegates: list[str] = []
        if delegatable:
            caller = org.agent_registry.get(self.agent_id)
            if caller:
                caller_delegates = caller.config.delegation.can_delegate_to

        results: list[str] = []
        for aid, agent in org.agent_registry.items():
            if aid == self.agent_id:
                continue
            cfg = agent.config
            if cfg.type.value in ("orchestrator", "huddle"):
                continue
            if type_filter and cfg.type.value != type_filter:
                continue
            if parent_filter and cfg.parent_id != parent_filter:
                continue
            if delegatable:
                if "*" not in caller_delegates and aid not in caller_delegates:
                    continue
            if query:
                searchable = f"{cfg.name} {cfg.title} {cfg.tagline}".lower()
                if query not in searchable:
                    continue

            line = (
                f"- **{cfg.name}** (`{aid}`): {cfg.title}"
                + (f" — {cfg.tagline}" if cfg.tagline else "")
                + f"\n  Type: {cfg.type.value}"
                + (f" | Parent: {cfg.parent_id}" if cfg.parent_id else "")
                + f" | Delegates to: {', '.join(cfg.delegation.can_delegate_to) or 'none'}"
            )
            results.append(line)

        if not results:
            return "No agents found matching your criteria."
        return f"Found {len(results)} agent(s):\n\n" + "\n\n".join(results)

    async def _execute_perf_tool(self, tool_name: str, arguments: str) -> str:
        """Execute a performance tracking tool call."""
        try:
            args = json.loads(arguments) if arguments else {}
        except json.JSONDecodeError:
            args = {}

        tracker = self._perf_tracker
        if not tracker:
            return "Error: Performance tracking is not available (no shared vault)."

        period = args.get("period", "")

        if tool_name == "perf_get_metrics":
            metrics = tracker.get_metrics(self.agent_id, period)
            return (
                f"## Performance Metrics — {metrics.period}\n\n"
                f"- Recommendations made: {metrics.recommendations_made}\n"
                f"- Recommendations adopted: {metrics.recommendations_adopted}\n"
                f"- Adoption rate: {metrics.adoption_rate:.0%}\n"
                f"- Outcomes tracked: {metrics.outcomes_tracked}\n"
                f"- Positive outcomes: {metrics.positive_outcomes}\n"
                f"- Positive outcome rate: {metrics.positive_outcome_rate:.0%}\n"
                f"- Average confidence: {metrics.avg_confidence:.2f}\n"
                f"- Disagreement rate: {metrics.disagreement_rate:.2f}\n"
                f"- Accuracy score: {metrics.accuracy_score:.2f}\n"
            )

        if tool_name == "perf_run_retro":
            retro = tracker.generate_retro(self.agent_id, period=period)
            lines = [f"## Retrospective — {retro.period}\n"]
            lines.append(f"**Agent:** {retro.agent_id}\n")
            if retro.insights:
                lines.append("### Insights")
                for insight in retro.insights:
                    lines.append(f"- {insight}")
            if retro.improvement_areas:
                lines.append("\n### Areas for Improvement")
                for area in retro.improvement_areas:
                    lines.append(f"- {area}")
            if not retro.insights and not retro.improvement_areas:
                lines.append("No significant patterns detected yet — keep building history.")
            return "\n".join(lines)

        return f"Error: Unknown performance tool: {tool_name}"

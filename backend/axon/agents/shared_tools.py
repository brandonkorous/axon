"""Shared vault tools — task and issue management for the organization."""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

from axon.vault.vault import VaultManager


# ── Tool schemas (for LLM tool-use) ─────────────────────────────────

TASK_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "task_create",
            "description": "Create a new task in the shared organization vault. Tasks track work items and assignments.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Short, descriptive title for the task",
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of what needs to be done",
                    },
                    "assignee": {
                        "type": "string",
                        "description": "Agent ID to assign this task to (e.g., 'raj', 'marcus', 'diana')",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["p0", "p1", "p2", "p3"],
                        "description": "Priority level: p0=critical, p1=high, p2=medium, p3=low",
                        "default": "p2",
                    },
                    "due_date": {
                        "type": "string",
                        "description": "Due date in YYYY-MM-DD format (optional)",
                    },
                    "labels": {
                        "type": "string",
                        "description": "Comma-separated labels (e.g., 'backend, auth, urgent')",
                    },
                    "parent_task": {
                        "type": "string",
                        "description": "Path to parent task if this is a subtask (optional)",
                    },
                    "conversation_id": {
                        "type": "string",
                        "description": "Conversation ID to deliver results back to when task completes (for async work)",
                    },
                    "owner": {
                        "type": "string",
                        "description": "Agent ID of who needs the result (gets notified on responses). Defaults to you.",
                    },
                },
                "required": ["title", "description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "task_update",
            "description": "Update an existing task's status, assignee, or priority.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the task file (e.g., 'tasks/2026-03-21-implement-auth.md')",
                    },
                    "status": {
                        "type": "string",
                        "enum": ["pending", "in_progress", "done", "blocked", "accepted"],
                        "description": "New status for the task",
                    },
                    "message": {
                        "type": "string",
                        "description": "Required message explaining why this status change is happening. This gets recorded in task activity.",
                    },
                    "assignee": {
                        "type": "string",
                        "description": "New assignee agent ID",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["p0", "p1", "p2", "p3"],
                        "description": "New priority level",
                    },
                },
                "required": ["path", "message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "task_list",
            "description": "List tasks from the shared vault, optionally filtered by status or assignee.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["pending", "in_progress", "done", "blocked", "accepted"],
                        "description": "Filter by status (optional — omit to list all)",
                    },
                    "assignee": {
                        "type": "string",
                        "description": "Filter by assignee agent ID (optional)",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "task_respond",
            "description": (
                "Add a response to a task thread. Use this to send results, "
                "updates, documents, or deliverables back to the task owner "
                "without closing the task."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the task file (e.g., 'tasks/2026-03-21-implement-auth.md')",
                    },
                    "content": {
                        "type": "string",
                        "description": "Response content — findings, results, updates, or questions",
                    },
                    "attachments": {
                        "type": "string",
                        "description": (
                            "JSON array of attachments. Each has 'type' (vault_path|url|document), "
                            "'path' (vault path or URL), and 'label' (short description). "
                            'Example: [{"type":"vault_path","path":"notes/analysis.md","label":"Full analysis"}]'
                        ),
                    },
                    "status": {
                        "type": "string",
                        "enum": ["pending", "in_progress", "done", "blocked", "accepted"],
                        "description": "Optionally update task status with your response",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
]

ISSUE_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "issue_create",
            "description": "Create a new issue in the shared organization vault. Issues track bugs, problems, and improvement requests.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Short, descriptive title for the issue",
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the issue",
                    },
                    "assignee": {
                        "type": "string",
                        "description": "Agent ID to assign this issue to",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["p0", "p1", "p2", "p3"],
                        "description": "Priority: p0=critical, p1=high, p2=medium, p3=low",
                        "default": "p2",
                    },
                    "labels": {
                        "type": "string",
                        "description": "Comma-separated labels (e.g., 'bug, vault, urgent')",
                    },
                    "parent_issue": {
                        "type": "string",
                        "description": "Path to parent issue if this is a sub-issue (optional)",
                    },
                },
                "required": ["title", "description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "issue_update",
            "description": "Update an existing issue's status, assignee, or priority.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the issue file (e.g., 'issues/42-vault-search-stale.md')",
                    },
                    "status": {
                        "type": "string",
                        "enum": ["open", "in_progress", "resolved", "closed"],
                        "description": "New status",
                    },
                    "assignee": {
                        "type": "string",
                        "description": "New assignee agent ID",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["p0", "p1", "p2", "p3"],
                        "description": "New priority",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "issue_comment",
            "description": "Add a comment to an existing issue.",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_path": {
                        "type": "string",
                        "description": "Path to the issue file (e.g., 'issues/42-vault-search-stale.md')",
                    },
                    "content": {
                        "type": "string",
                        "description": "The comment text (markdown supported)",
                    },
                },
                "required": ["issue_path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "issue_list",
            "description": "List issues from the shared vault, optionally filtered.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["open", "in_progress", "resolved", "closed"],
                        "description": "Filter by status (optional)",
                    },
                    "assignee": {
                        "type": "string",
                        "description": "Filter by assignee (optional)",
                    },
                    "label": {
                        "type": "string",
                        "description": "Filter by label (optional)",
                    },
                },
                "required": [],
            },
        },
    },
]

KNOWLEDGE_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "knowledge_share",
            "description": (
                "Share knowledge, documents, or key information with the team. "
                "Creates a knowledge entry in the shared vault and automatically "
                "creates review tasks so target advisors wake up, read it, and "
                "extract learnings relevant to their domain. Use this when an "
                "advisor commits to sharing information, a document needs team "
                "review, or key insights should be distributed across the team."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Short, descriptive title for the knowledge entry",
                    },
                    "content": {
                        "type": "string",
                        "description": (
                            "The knowledge content to share — key information, "
                            "document summary, analysis, data points, or insights"
                        ),
                    },
                    "from_advisor": {
                        "type": "string",
                        "description": "Agent ID of the advisor sharing this knowledge",
                    },
                    "for_advisors": {
                        "type": "string",
                        "description": (
                            "Comma-separated agent IDs who should review this "
                            "(e.g., 'raj, diana'). Use 'all' to share with everyone."
                        ),
                    },
                    "knowledge_type": {
                        "type": "string",
                        "enum": [
                            "document", "analysis", "strategy",
                            "data", "decision", "insight",
                        ],
                        "description": "Type of knowledge being shared",
                        "default": "document",
                    },
                    "review_prompt": {
                        "type": "string",
                        "description": (
                            "Specific guidance for reviewers — what to focus on, "
                            "what to extract, what applies to their domain "
                            "(optional — a sensible default is generated)"
                        ),
                    },
                    "labels": {
                        "type": "string",
                        "description": "Comma-separated labels (e.g., 'fundraising, strategy, urgent')",
                    },
                },
                "required": ["title", "content", "from_advisor", "for_advisors"],
            },
        },
    },
]


# ── Executor ────────────────────────────────────────────────────────


class SharedVaultToolExecutor:
    """Executes task, issue, and knowledge tool calls against the shared org vault.

    Achievements are auto-generated when a parent task reaches 'accepted' status.
    """

    def __init__(
        self,
        shared_vault: VaultManager,
        agent_id: str,
        conversation_manager: Any = None,
        ws_target: str = "",
        org_id: str = "",
        advisor_ids: list[str] | None = None,
    ):
        self.vault = shared_vault
        self.agent_id = agent_id
        self.conversation_manager = conversation_manager
        self.ws_target = ws_target or agent_id
        self.org_id = org_id
        self.advisor_ids = advisor_ids or []

    async def execute(self, tool_name: str, arguments: str) -> str:
        """Execute a shared vault tool call."""
        try:
            args = json.loads(arguments)
        except json.JSONDecodeError:
            return f"Error: Invalid JSON arguments: {arguments}"

        handlers = {
            "task_create": self._task_create,
            "task_update": self._task_update,
            "task_respond": self._task_respond,
            "task_list": self._task_list,
            "issue_create": self._issue_create,
            "issue_update": self._issue_update,
            "issue_comment": self._issue_comment,
            "knowledge_share": self._knowledge_share,
            "issue_list": self._issue_list,
        }

        handler = handlers.get(tool_name)
        if not handler:
            return f"Error: Unknown shared tool: {tool_name}"

        try:
            return await handler(args)
        except Exception as e:
            return f"Error executing {tool_name}: {e}"

    # ── Tasks ───────────────────────────────────────────────────────

    async def _task_create(self, args: dict) -> str:
        title = args["title"]
        slug = _slugify(title)
        today_str = str(date.today())
        path = f"tasks/{today_str}-{slug}.md"

        # Prevent overwriting existing tasks — return the existing one instead
        try:
            existing_meta, _ = self.vault.read_file(path)
            existing_status = existing_meta.get("status", "")
            return (
                f"Task already exists: [[{path}]] "
                f"(status: {existing_status}, assignee: {existing_meta.get('assignee', 'unassigned')}). "
                f"Use task_update to modify it."
            )
        except FileNotFoundError:
            pass  # Good — no collision

        labels_raw = args.get("labels", "")
        labels = [l.strip() for l in labels_raw.split(",") if l.strip()] if labels_raw else []

        assignee = args.get("assignee", "")
        # Auto-set in_progress when task has an assignee
        status = "in_progress" if assignee else "pending"

        metadata = {
            "name": title,
            "type": "task",
            "owner": args.get("owner", self.agent_id),
            "assignee": assignee,
            "status": status,
            "priority": args.get("priority", "p2"),
            "due_date": args.get("due_date", ""),
            "parent_task": args.get("parent_task", ""),
            "labels": labels,
            "conversation_id": args.get("conversation_id", "")
            or (self.conversation_manager.active_id if self.conversation_manager else ""),
            "ws_target": self.ws_target,
            "created_by": self.agent_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "responses": [],
        }

        content = f"# {title}\n\n{args['description']}"
        self.vault.write_file(path, metadata, content)

        # Update index
        self.vault._update_branch_index("tasks", slug, title)

        # Trigger immediate execution when task has an assignee
        if assignee:
            await self._trigger_task_execution(assignee)

        display_assignee = assignee or "unassigned"
        return f"Task created: [[{path}]] (assigned to {display_assignee}, status: {status}, priority {metadata['priority']})"

    async def _task_update(self, args: dict) -> str:
        path = args["path"]
        try:
            metadata, body = self.vault.read_file(path)
        except FileNotFoundError:
            return f"Task not found: {path}"

        changes = []
        for field in ("status", "assignee", "priority"):
            if field in args and args[field]:
                old_val = metadata.get(field, "")
                metadata[field] = args[field]
                changes.append(f"{field}: {old_val} → {args[field]}")

        # Record activity message for status changes
        message = args.get("message", "")
        if message:
            activity_entry = {
                "from": self.agent_id,
                "content": message,
                "attachments": [],
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "type": "status_change",
                "status_to": args.get("status", ""),
            }
            if "responses" not in metadata:
                metadata["responses"] = []
            metadata["responses"].append(activity_entry)

        metadata["updated_at"] = datetime.utcnow().isoformat() + "Z"
        self.vault.write_file(path, metadata, body)

        # Trigger immediate execution when task becomes in_progress
        new_status = args.get("status", "")
        assignee = metadata.get("assignee", "")
        if new_status == "in_progress" and assignee:
            await self._trigger_task_execution(assignee)

        # Auto-generate achievement for accepted parent tasks
        if args.get("status") == "accepted":
            await self._maybe_create_achievement(path, metadata)

        return f"Task updated: {path} ({', '.join(changes)})"

    async def _task_respond(self, args: dict) -> str:
        path = args["path"]
        try:
            metadata, body = self.vault.read_file(path)
        except FileNotFoundError:
            return f"Task not found: {path}"

        # Parse attachments if provided
        attachments: list[dict[str, str]] = []
        attachments_raw = args.get("attachments", "")
        if attachments_raw:
            try:
                attachments = json.loads(attachments_raw)
            except json.JSONDecodeError:
                return "Error: Invalid JSON in attachments parameter"

        response_entry = {
            "from": self.agent_id,
            "content": args["content"],
            "attachments": attachments,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        if "responses" not in metadata:
            metadata["responses"] = []
        metadata["responses"].append(response_entry)
        metadata["updated_at"] = datetime.utcnow().isoformat() + "Z"

        # Optionally update status with the response
        if args.get("status"):
            metadata["status"] = args["status"]

        self.vault.write_file(path, metadata, body)

        owner = metadata.get("owner", "")
        total = len(metadata["responses"])
        return f"Response added to {path} (owner: {owner or 'unset'}, {total} response{'s' if total != 1 else ''})"

    async def _trigger_task_execution(self, target_agent_id: str = "") -> None:
        """Trigger the scheduler to process tasks for an agent after current response completes."""
        import asyncio

        from axon.scheduler import scheduler

        agent_id = target_agent_id or self.agent_id
        org_id = self.org_id
        if not org_id:
            return

        async def _delayed_trigger() -> None:
            # Wait for the current agent.process() call to finish and release the lock
            await asyncio.sleep(5)
            await scheduler.trigger_task_execution(org_id, agent_id)

        asyncio.create_task(_delayed_trigger())

    async def _task_list(self, args: dict) -> str:
        tasks_dir = Path(self.vault.vault_path) / "tasks"
        if not tasks_dir.exists():
            return "No tasks found."

        tasks = []
        for md_file in sorted(tasks_dir.glob("*.md"), reverse=True):
            if md_file.name.endswith("-index.md"):
                continue
            try:
                metadata, _ = self.vault.read_file(f"tasks/{md_file.name}")
                # Apply filters
                if args.get("status") and metadata.get("status") != args["status"]:
                    continue
                if args.get("assignee") and metadata.get("assignee") != args["assignee"]:
                    continue
                tasks.append(metadata | {"path": f"tasks/{md_file.name}"})
            except Exception:
                continue

        if not tasks:
            filters = []
            if args.get("status"):
                filters.append(f"status={args['status']}")
            if args.get("assignee"):
                filters.append(f"assignee={args['assignee']}")
            filter_str = f" (filters: {', '.join(filters)})" if filters else ""
            return f"No tasks found{filter_str}."

        lines = []
        for t in tasks[:20]:
            status_icon = {
                "pending": "⏳", "in_progress": "🔄", "done": "✅",
                "blocked": "🚫", "accepted": "✅",
            }.get(t.get("status", ""), "")
            assignee = t.get("assignee", "unassigned") or "unassigned"
            # Flag tasks assigned to the requesting agent
            if assignee == self.agent_id:
                assignee = f"{assignee} (you)"
            lines.append(
                f"- {status_icon} **{t.get('name', '?')}** [{t.get('priority', '?')}] "
                f"→ {assignee} (`{t['path']}`)"
            )
        return "\n".join(lines)

    # ── Issues ──────────────────────────────────────────────────────

    async def _issue_create(self, args: dict) -> str:
        title = args["title"]
        slug = _slugify(title)
        issue_id = self._next_issue_id()

        path = f"issues/{issue_id}-{slug}.md"

        labels_raw = args.get("labels", "")
        labels = [l.strip() for l in labels_raw.split(",") if l.strip()] if labels_raw else []

        metadata = {
            "name": title,
            "type": "issue",
            "id": issue_id,
            "assignee": args.get("assignee", ""),
            "status": "open",
            "priority": args.get("priority", "p2"),
            "labels": labels,
            "parent_issue": args.get("parent_issue", ""),
            "created_by": self.agent_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
        }

        content = f"# #{issue_id}: {title}\n\n{args['description']}"
        self.vault.write_file(path, metadata, content)

        # Update index
        self.vault._update_branch_index("issues", f"{issue_id}-{slug}", title)

        assignee = args.get("assignee", "unassigned")
        return f"Issue #{issue_id} created: [[{path}]] (assigned to {assignee}, priority {metadata['priority']})"

    async def _issue_update(self, args: dict) -> str:
        path = args["path"]
        try:
            metadata, body = self.vault.read_file(path)
        except FileNotFoundError:
            return f"Issue not found: {path}"

        changes = []
        for field in ("status", "assignee", "priority"):
            if field in args and args[field]:
                old_val = metadata.get(field, "")
                metadata[field] = args[field]
                changes.append(f"{field}: {old_val} → {args[field]}")

        metadata["updated_at"] = datetime.utcnow().isoformat() + "Z"
        self.vault.write_file(path, metadata, body)
        return f"Issue updated: {path} ({', '.join(changes)})"

    async def _issue_comment(self, args: dict) -> str:
        issue_path = args["issue_path"]

        # Verify issue exists
        try:
            self.vault.read_file(issue_path)
        except FileNotFoundError:
            return f"Issue not found: {issue_path}"

        # Create comment file
        ts = datetime.utcnow()
        ts_str = ts.strftime("%Y%m%d%H%M%S")
        issue_dir = issue_path.removesuffix(".md")
        comment_path = f"{issue_dir}/comments/{ts_str}.md"

        metadata = {
            "author": self.agent_id,
            "type": "comment",
            "created_at": ts.isoformat() + "Z",
        }

        self.vault.write_file(comment_path, metadata, args["content"])
        return f"Comment added to {issue_path}: [[{comment_path}]]"

    async def _issue_list(self, args: dict) -> str:
        issues_dir = Path(self.vault.vault_path) / "issues"
        if not issues_dir.exists():
            return "No issues found."

        issues = []
        for md_file in sorted(issues_dir.glob("*.md"), reverse=True):
            if md_file.name.endswith("-index.md"):
                continue
            try:
                metadata, _ = self.vault.read_file(f"issues/{md_file.name}")
                # Apply filters
                if args.get("status") and metadata.get("status") != args["status"]:
                    continue
                if args.get("assignee") and metadata.get("assignee") != args["assignee"]:
                    continue
                if args.get("label"):
                    issue_labels = metadata.get("labels", [])
                    if isinstance(issue_labels, str):
                        issue_labels = [l.strip() for l in issue_labels.split(",")]
                    if args["label"] not in issue_labels:
                        continue
                issues.append(metadata | {"path": f"issues/{md_file.name}"})
            except Exception:
                continue

        if not issues:
            return "No issues found matching filters."

        lines = []
        for i in issues[:20]:
            status_icon = {"open": "🔴", "in_progress": "🟡", "resolved": "🟢", "closed": "⚫"}.get(i.get("status", ""), "")
            assignee = i.get("assignee", "unassigned") or "unassigned"
            issue_id = i.get("id", "?")
            lines.append(
                f"- {status_icon} **#{issue_id}: {i.get('name', '?')}** [{i.get('priority', '?')}] "
                f"→ {assignee} (`{i['path']}`)"
            )
        return "\n".join(lines)

    # ── Achievements (auto-generated) ──────────────────────────────────

    async def _maybe_create_achievement(self, task_path: str, task_metadata: dict) -> None:
        """Auto-create an achievement if this is a parent task with completed children."""
        tasks_dir = Path(self.vault.vault_path) / "tasks"
        if not tasks_dir.exists():
            return

        children = []
        for md_file in tasks_dir.glob("*.md"):
            if md_file.name.endswith("-index.md"):
                continue
            try:
                meta, _ = self.vault.read_file(f"tasks/{md_file.name}")
                if meta.get("parent_task") == task_path:
                    children.append(meta)
            except Exception:
                continue

        if not children:
            return  # Leaf task — no achievement

        title = task_metadata.get("name", "Untitled")
        slug = _slugify(title)
        today_str = str(date.today())
        achievement_path = f"achievements/{today_str}-{slug}.md"

        # Collect agents involved
        agents: set[str] = set()
        agents.add(task_metadata.get("assignee", ""))
        agents.add(task_metadata.get("owner", ""))
        for child in children:
            agents.add(child.get("assignee", ""))
        agents.discard("")

        # Collect linked task paths
        linked_tasks = [task_path]
        for md_file in tasks_dir.glob("*.md"):
            if md_file.name.endswith("-index.md"):
                continue
            try:
                meta, _ = self.vault.read_file(f"tasks/{md_file.name}")
                if meta.get("parent_task") == task_path:
                    linked_tasks.append(f"tasks/{md_file.name}")
            except Exception:
                continue

        # Generate LLM summary
        summary = await self._generate_achievement_summary(title, task_metadata, children)

        metadata = {
            "name": title,
            "type": "achievement",
            "agents_involved": sorted(agents),
            "linked_tasks": linked_tasks,
            "linked_issues": [],
            "impact": "",
            "date": today_str,
            "created_by": "system",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "auto_generated": True,
        }

        self.vault.write_file(achievement_path, metadata, f"# {title}\n\n{summary}")
        self.vault._update_branch_index("achievements", slug, title)

    async def _generate_achievement_summary(
        self, title: str, parent: dict, children: list[dict],
    ) -> str:
        """Use internal LLM to generate a positive achievement summary."""
        try:
            from axon.agents.provider import complete
            from axon.config import settings

            child_summaries = []
            for c in children[:10]:  # Cap context
                child_summaries.append(
                    f"- {c.get('name', '?')} (assigned to {c.get('assignee', '?')}, "
                    f"status: {c.get('status', '?')})"
                )

            prompt = (
                f"Write a brief, celebratory achievement summary (2-3 sentences) "
                f"for this completed initiative.\n\n"
                f"**Initiative:** {title}\n"
                f"**Description:** {str(parent.get('body', 'No description'))[:500]}\n"
                f"**Subtasks completed:**\n" + "\n".join(child_summaries) + "\n\n"
                f"Frame it as a positive milestone — what was accomplished and why "
                f"it matters. Be concise, specific, and celebratory. Do not use "
                f"generic filler."
            )

            result = await complete(
                model=settings.default_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.7,
            )
            return result.get("content", "").strip()
        except Exception:
            # Fallback if LLM unavailable
            child_count = len(children)
            assignees = sorted(
                set(c.get("assignee", "?") for c in children if c.get("assignee"))
            )
            return (
                f"Completed **{title}** — successfully delivered across "
                f"{child_count} subtask{'s' if child_count != 1 else ''} "
                f"with contributions from {', '.join(assignees)}."
            )

    # ── Knowledge Sharing ────────────────────────────────────────────

    async def _knowledge_share(self, args: dict) -> str:
        title = args["title"]
        slug = _slugify(title)
        today_str = str(date.today())
        path = f"knowledge/{today_str}-{slug}.md"

        from_advisor = args.get("from_advisor", self.agent_id)
        for_raw = args.get("for_advisors", "all")
        knowledge_type = args.get("knowledge_type", "document")
        review_prompt = args.get("review_prompt", "")

        labels_raw = args.get("labels", "")
        labels = [l.strip() for l in labels_raw.split(",") if l.strip()] if labels_raw else []

        # Resolve "all" to actual advisor IDs
        if for_raw.strip().lower() == "all":
            advisor_pool = self.advisor_ids
            if not advisor_pool and self.org_id:
                # Resolve dynamically from registry
                import axon.registry as registry
                org = registry.org_registry.get(self.org_id)
                if org:
                    advisor_pool = list(org.agent_registry.keys())
            target_advisors = [a for a in advisor_pool if a != from_advisor]
        else:
            target_advisors = [a.strip() for a in for_raw.split(",") if a.strip()]

        metadata = {
            "name": title,
            "type": "knowledge",
            "knowledge_type": knowledge_type,
            "from": from_advisor,
            "for": target_advisors,
            "labels": labels,
            "status": "shared",
            "review_prompt": review_prompt,
            "created_by": self.agent_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }

        content = f"# {title}\n\n**Shared by:** {from_advisor}\n\n{args['content']}"
        self.vault.write_file(path, metadata, content)
        self.vault._update_branch_index("knowledge", slug, title)

        # Create review tasks for each target advisor
        created_tasks = []
        for advisor_id in target_advisors:
            default_prompt = (
                f"Review the shared knowledge document [[{path}]] from {from_advisor}. "
                f"Extract key insights relevant to your domain and save them to your vault."
            )
            task_title = f"Review: {title}"
            task_slug = _slugify(task_title)
            task_path = f"tasks/{today_str}-{task_slug}-{advisor_id}.md"

            # Skip if task already exists
            try:
                self.vault.read_file(task_path)
                continue
            except FileNotFoundError:
                pass

            task_meta = {
                "name": task_title,
                "type": "task",
                "assignee": advisor_id,
                "status": "in_progress",
                "priority": "p2",
                "labels": ["knowledge-review"],
                "knowledge_ref": path,
                "conversation_id": (
                    self.conversation_manager.active_id
                    if self.conversation_manager else ""
                ),
                "ws_target": self.ws_target,
                "created_by": self.agent_id,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.utcnow().isoformat() + "Z",
            }

            task_content = (
                f"# {task_title}\n\n"
                f"**Source:** [[{path}]]\n"
                f"**From:** {from_advisor}\n\n"
                f"## Instructions\n\n"
                f"{review_prompt or default_prompt}\n\n"
                f"After reviewing:\n"
                f"1. Read the knowledge document from the shared vault\n"
                f"2. Extract insights relevant to your expertise\n"
                f"3. Save key takeaways to your own vault under learnings/\n"
                f"4. Note any concerns, gaps, or action items from your perspective"
            )
            self.vault.write_file(task_path, task_meta, task_content)
            created_tasks.append(advisor_id)

            # Trigger immediate execution
            await self._trigger_task_execution(advisor_id)

        reviewers = ", ".join(created_tasks) if created_tasks else "none (already pending)"
        return (
            f"Knowledge shared: [[{path}]] — {title}\n"
            f"Review tasks created for: {reviewers}"
        )

    def _next_issue_id(self) -> int:
        """Get and increment the auto-increment issue ID."""
        counter_path = Path(self.vault.vault_path) / "issues" / ".next_id"
        counter_path.parent.mkdir(parents=True, exist_ok=True)

        if counter_path.exists():
            current = int(counter_path.read_text().strip())
        else:
            current = 1

        counter_path.write_text(str(current + 1), encoding="utf-8")
        return current


# ── Helpers ─────────────────────────────────────────────────────────


def _slugify(text: str, max_length: int = 50) -> str:
    """Convert text to a URL-safe slug."""
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:max_length]

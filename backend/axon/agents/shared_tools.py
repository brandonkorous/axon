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
                        "enum": ["pending", "in_progress", "planned", "awaiting_approval", "approved", "declined", "executing", "done", "blocked", "failed"],
                        "description": "New status for the task",
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
                "required": ["path"],
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
                        "enum": ["pending", "in_progress", "planned", "awaiting_approval", "approved", "declined", "executing", "done", "blocked", "failed"],
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

ACHIEVEMENT_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "achievement_create",
            "description": "Record an achievement or milestone for the organization. Use when a significant goal is reached, a project ships, or a notable outcome occurs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Short title for the achievement",
                    },
                    "description": {
                        "type": "string",
                        "description": "What was achieved and why it matters",
                    },
                    "impact": {
                        "type": "string",
                        "description": "Business impact or significance (e.g., 'Projected 20% revenue increase')",
                    },
                    "agents_involved": {
                        "type": "string",
                        "description": "Comma-separated agent IDs who contributed (e.g., 'marcus, raj')",
                    },
                    "linked_tasks": {
                        "type": "string",
                        "description": "Comma-separated wikilinks to related tasks (optional)",
                    },
                    "linked_issues": {
                        "type": "string",
                        "description": "Comma-separated wikilinks to related issues (optional)",
                    },
                },
                "required": ["title", "description"],
            },
        },
    },
]


# ── Executor ────────────────────────────────────────────────────────


class SharedVaultToolExecutor:
    """Executes task, issue, and achievement tool calls against the shared org vault."""

    def __init__(
        self,
        shared_vault: VaultManager,
        agent_id: str,
        conversation_manager: Any = None,
        ws_target: str = "",
        org_id: str = "",
    ):
        self.vault = shared_vault
        self.agent_id = agent_id
        self.conversation_manager = conversation_manager
        self.ws_target = ws_target or agent_id
        self.org_id = org_id

    async def execute(self, tool_name: str, arguments: str) -> str:
        """Execute a shared vault tool call."""
        try:
            args = json.loads(arguments)
        except json.JSONDecodeError:
            return f"Error: Invalid JSON arguments: {arguments}"

        handlers = {
            "task_create": self._task_create,
            "task_update": self._task_update,
            "task_list": self._task_list,
            "issue_create": self._issue_create,
            "issue_update": self._issue_update,
            "issue_comment": self._issue_comment,
            "issue_list": self._issue_list,
            "achievement_create": self._achievement_create,
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

        metadata["updated_at"] = datetime.utcnow().isoformat() + "Z"
        self.vault.write_file(path, metadata, body)

        # Trigger immediate execution when task becomes in_progress
        new_status = args.get("status", "")
        assignee = metadata.get("assignee", "")
        if new_status == "in_progress" and assignee:
            await self._trigger_task_execution(assignee)

        return f"Task updated: {path} ({', '.join(changes)})"

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
                "pending": "⏳", "in_progress": "🔄", "planned": "📋",
                "awaiting_approval": "🔔", "approved": "✅", "declined": "❌",
                "executing": "⚙️", "done": "✅", "blocked": "🚫", "failed": "💥",
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

    # ── Achievements ─────────────────────────────────────────────────

    async def _achievement_create(self, args: dict) -> str:
        title = args["title"]
        slug = _slugify(title)
        today_str = str(date.today())
        path = f"achievements/{today_str}-{slug}.md"

        agents_raw = args.get("agents_involved", "")
        agents_involved = [a.strip() for a in agents_raw.split(",") if a.strip()] if agents_raw else []

        linked_tasks_raw = args.get("linked_tasks", "")
        linked_tasks = [t.strip() for t in linked_tasks_raw.split(",") if t.strip()] if linked_tasks_raw else []

        linked_issues_raw = args.get("linked_issues", "")
        linked_issues = [i.strip() for i in linked_issues_raw.split(",") if i.strip()] if linked_issues_raw else []

        metadata = {
            "name": title,
            "type": "achievement",
            "agents_involved": agents_involved,
            "linked_tasks": linked_tasks,
            "linked_issues": linked_issues,
            "impact": args.get("impact", ""),
            "date": today_str,
            "created_by": self.agent_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }

        content = f"# {title}\n\n{args['description']}"
        if args.get("impact"):
            content += f"\n\n## Impact\n{args['impact']}"

        self.vault.write_file(path, metadata, content)
        self.vault._update_branch_index("achievements", slug, title)

        return f"Achievement recorded: [[{path}]] — {title}"

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

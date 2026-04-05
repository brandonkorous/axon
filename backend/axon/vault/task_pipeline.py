"""Task pipeline — pre/post processing for automatic task management.

Replaces agent-facing task tools with automatic pipeline:
- Pre: injects active task context into agent prompt
- Post: local LLM decides if tasks should be created/updated
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from axon.logging import get_logger
from axon.vault.vault import VaultManager

logger = get_logger(__name__)

STATUS_ICONS = {
    "pending": "⏳", "in_progress": "🔄", "done": "✅",
    "blocked": "🚫", "accepted": "✅",
}


async def recall_tasks(
    shared_vault: VaultManager,
    agent_id: str,
) -> str:
    """Pre-processing: return active tasks assigned to this agent as context."""
    tasks_dir = Path(shared_vault.vault_path) / "tasks"
    if not tasks_dir.exists():
        return ""

    lines: list[str] = []
    for md_file in sorted(tasks_dir.glob("*.md"), reverse=True):
        if md_file.name.endswith("-index.md"):
            continue
        try:
            metadata, _ = shared_vault.read_file(f"tasks/{md_file.name}")
        except Exception:
            continue
        if metadata.get("assignee") != agent_id:
            continue
        status = metadata.get("status", "")
        if status not in ("pending", "in_progress", "blocked"):
            continue
        icon = STATUS_ICONS.get(status, "")
        title = metadata.get("name", md_file.stem)
        priority = metadata.get("priority", "p2")
        path = f"tasks/{md_file.name}"

        # Include last activity if any
        responses = metadata.get("responses", [])
        last_activity = ""
        if responses:
            last = responses[-1]
            last_activity = f" — last: {last.get('content', '')[:80]}"

        lines.append(f"- {icon} **{title}** [{priority}] `{path}`{last_activity}")

    if not lines:
        return ""
    return "## Your Active Tasks\n\n" + "\n".join(lines[:10])


async def process_turn_for_tasks(
    user_message: str,
    agent_response: str,
    agent_id: str,
    shared_vault: VaultManager,
    task_context: str,
    memory_model: str = "",
    org_id: str = "",
) -> None:
    """Post-processing: local LLM decides if tasks should be created/updated."""
    if not memory_model:
        return

    from axon.agents.provider import complete

    prompt = _build_task_prompt(user_message, agent_response, task_context)

    try:
        result = await complete(prompt, model=memory_model, max_tokens=512, temperature=0.1)
        content = result.get("content", "").strip()
        actions = _parse_task_actions(content)
        if not actions:
            return
        for action in actions:
            await _execute_task_action(action, agent_id, shared_vault, org_id)
    except Exception as e:
        logger.debug("Task pipeline failed (non-critical): %s", e)


def _build_task_prompt(
    user_message: str,
    agent_response: str,
    task_context: str,
) -> str:
    """Build the prompt for the local LLM to analyze the turn for task actions."""
    active = task_context or "No active tasks."
    return (
        "You are a task manager for an AI agent. Analyze this conversation turn "
        "and decide if any task actions are needed.\n\n"
        f"## Active Tasks\n{active}\n\n"
        f"## User Message\n{user_message}\n\n"
        f"## Agent Response\n{agent_response[:500]}\n\n"
        "Respond with JSON only:\n"
        "```json\n"
        '{"actions": [\n'
        '  {"type": "create", "title": "...", "description": "...", "priority": "p2"},\n'
        '  {"type": "update", "path": "tasks/...", "status": "done", '
        '"message": "Completed: ..."},\n'
        '  {"type": "respond", "path": "tasks/...", "content": "Progress: ..."}\n'
        "]}\n```\n\n"
        "Rules:\n"
        "- Only create tasks for substantial new work (not simple questions/answers)\n"
        "- Update existing tasks if the agent completed or made progress on them\n"
        "- If nothing task-worthy happened, respond: {\"actions\": []}\n"
        "- Keep titles short (under 60 chars)\n"
        "- Skip greetings, small talk, and routine Q&A"
    )


def _parse_task_actions(content: str) -> list[dict[str, Any]]:
    """Parse local LLM response into task actions."""
    import re
    json_match = re.search(r"\{.*\}", content, re.DOTALL)
    if not json_match:
        return []
    try:
        data = json.loads(json_match.group())
        actions = data.get("actions", [])
        return actions if isinstance(actions, list) else []
    except (json.JSONDecodeError, KeyError):
        return []


def _slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    import re as _re
    slug = _re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:50]


async def _execute_task_action(
    action: dict[str, Any],
    agent_id: str,
    shared_vault: VaultManager,
    org_id: str,
) -> None:
    """Execute a single task action against the shared vault."""
    action_type = action.get("type", "")

    if action_type == "create":
        title = action.get("title", "")
        if not title:
            return
        slug = _slugify(title)
        today_str = str(date.today())
        path = f"tasks/{today_str}-{slug}.md"

        # Skip if exists
        try:
            shared_vault.read_file(path)
            return
        except FileNotFoundError:
            pass

        metadata = {
            "name": title,
            "type": "task",
            "owner": agent_id,
            "assignee": agent_id,
            "status": "in_progress",
            "priority": action.get("priority", "p2"),
            "labels": [],
            "created_by": agent_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "responses": [],
        }
        content = f"# {title}\n\n{action.get('description', '')}"
        shared_vault.write_file(path, metadata, content)
        shared_vault._update_branch_index("tasks", slug, title)
        logger.debug("Task pipeline created: %s", path)

    elif action_type == "update":
        path = action.get("path", "")
        if not path:
            return
        try:
            metadata, body = shared_vault.read_file(path)
        except FileNotFoundError:
            return

        if action.get("status"):
            metadata["status"] = action["status"]
        if action.get("message"):
            entry = {
                "from": agent_id,
                "content": action["message"],
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "type": "status_change",
                "status_to": action.get("status", ""),
            }
            metadata.setdefault("responses", []).append(entry)
        metadata["updated_at"] = datetime.utcnow().isoformat() + "Z"
        shared_vault.write_file(path, metadata, body)
        logger.debug("Task pipeline updated: %s", path)

    elif action_type == "respond":
        path = action.get("path", "")
        if not path:
            return
        try:
            metadata, body = shared_vault.read_file(path)
        except FileNotFoundError:
            return
        entry = {
            "from": agent_id,
            "content": action.get("content", ""),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        metadata.setdefault("responses", []).append(entry)
        metadata["updated_at"] = datetime.utcnow().isoformat() + "Z"
        shared_vault.write_file(path, metadata, body)
        logger.debug("Task pipeline responded: %s", path)

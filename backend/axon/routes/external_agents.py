"""External agent routes — REST API for host-side runners."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import axon.registry as registry

org_router = APIRouter()


class PlanSubmission(BaseModel):
    plan: str
    files_affected: list[str] = []


class ResultSubmission(BaseModel):
    success: bool
    summary: str
    diff: str = ""
    error: str | None = None


class ActivityUpdate(BaseModel):
    phase: str  # "idle" | "generating_plan" | "awaiting_approval" | "executing"
    task_name: str = ""
    detail: str = ""


def _get_external_agent(org_id: str, agent_id: str):
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Organization not found: {org_id}")
    agent = org.agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(404, f"Agent not found: {agent_id}")
    if not getattr(agent, "is_external", False):
        raise HTTPException(400, f"Agent '{agent_id}' is not an external agent")
    return org, agent


def _get_shared_vault(org):
    if not org.shared_vault:
        raise HTTPException(404, "No shared vault for this organization")
    return org.shared_vault


def _parse_inbox(agent) -> list[dict[str, Any]]:
    """Read pending tasks from the agent's inbox."""
    inbox_dir = Path(agent.vault.vault_path) / "inbox"
    if not inbox_dir.exists():
        return []

    tasks = []
    for md_file in sorted(inbox_dir.glob("*.md"), reverse=True):
        if md_file.name.endswith("-index.md"):
            continue
        try:
            metadata, body = agent.vault.read_file(f"inbox/{md_file.name}")
            metadata["path"] = f"inbox/{md_file.name}"
            metadata["body"] = body
            tasks.append(metadata)
        except Exception:
            continue
    return tasks


def _find_shared_task(vault, delegation_ref: str | None = None,
                      assignee: str | None = None) -> tuple[str, dict, str] | None:
    """Find a shared vault task by delegation_ref or assignee."""
    tasks_dir = Path(vault.vault_path) / "tasks"
    if not tasks_dir.exists():
        return None

    for md_file in sorted(tasks_dir.glob("*.md"), reverse=True):
        if md_file.name.endswith("-index.md"):
            continue
        try:
            metadata, body = vault.read_file(f"tasks/{md_file.name}")
            path = f"tasks/{md_file.name}"
            if delegation_ref and metadata.get("delegation_ref") == delegation_ref:
                return path, metadata, body
            if assignee and metadata.get("assignee") == assignee:
                if metadata.get("status") in ("pending", "approved"):
                    return path, metadata, body
        except Exception:
            continue
    return None


@org_router.get("/{agent_id}/tasks")
async def list_external_tasks(org_id: str, agent_id: str):
    """Return pending + approved tasks for the external agent."""
    org, agent = _get_external_agent(org_id, agent_id)
    agent.last_poll_time = datetime.utcnow()
    vault = _get_shared_vault(org)

    # Get inbox tasks
    inbox_tasks = _parse_inbox(agent)

    # Get shared vault tasks assigned to this agent
    tasks_dir = Path(vault.vault_path) / "tasks"
    shared_tasks = []
    if tasks_dir.exists():
        for md_file in sorted(tasks_dir.glob("*.md"), reverse=True):
            if md_file.name.endswith("-index.md"):
                continue
            try:
                metadata, body = vault.read_file(f"tasks/{md_file.name}")
                if metadata.get("assignee") == agent_id:
                    metadata["path"] = f"tasks/{md_file.name}"
                    metadata["body"] = body
                    shared_tasks.append(metadata)
            except Exception:
                continue

    return {"inbox": inbox_tasks, "tasks": shared_tasks}


@org_router.post("/{agent_id}/tasks/{task_path:path}/plan")
async def submit_plan(org_id: str, agent_id: str, task_path: str, data: PlanSubmission):
    """Runner submits a plan for a task. Updates status to awaiting_approval."""
    org, agent = _get_external_agent(org_id, agent_id)
    vault = _get_shared_vault(org)

    if not task_path.startswith("tasks/"):
        task_path = f"tasks/{task_path}"

    try:
        metadata, body = vault.read_file(task_path)
    except FileNotFoundError:
        raise HTTPException(404, f"Task not found: {task_path}")

    metadata["status"] = "awaiting_approval"
    metadata["plan_content"] = data.plan
    metadata["files_affected"] = data.files_affected
    metadata["updated_at"] = datetime.utcnow().isoformat() + "Z"
    vault.write_file(task_path, metadata, body)

    # Notify the delegating agent via their inbox
    delegated_by = metadata.get("created_by", "")
    if delegated_by:
        delegating_agent = org.agent_registry.get(delegated_by)
        if delegating_agent and hasattr(delegating_agent, "vault"):
            today_str = str(date.today())
            notif_path = f"inbox/{today_str}-plan-ready-{agent_id}.md"
            notif_meta = {
                "from": agent_id,
                "date": today_str,
                "type": "plan_ready",
                "status": "pending",
                "task_ref": task_path,
            }
            notif_body = (
                f"## Plan Ready for Review\n\n"
                f"**Task:** {metadata.get('name', task_path)}\n\n"
                f"**Files affected:** {', '.join(data.files_affected) or 'N/A'}\n\n"
                f"### Plan\n{data.plan}\n"
            )
            delegating_agent.vault.write_file(notif_path, notif_meta, notif_body)

    return {"status": "awaiting_approval", "task_path": task_path}


@org_router.post("/{agent_id}/tasks/{task_path:path}/result")
async def submit_result(org_id: str, agent_id: str, task_path: str, data: ResultSubmission):
    """Runner reports execution result. Updates task to done or failed."""
    org, agent = _get_external_agent(org_id, agent_id)
    vault = _get_shared_vault(org)

    if not task_path.startswith("tasks/"):
        task_path = f"tasks/{task_path}"

    try:
        metadata, body = vault.read_file(task_path)
    except FileNotFoundError:
        raise HTTPException(404, f"Task not found: {task_path}")

    metadata["status"] = "done" if data.success else "failed"
    metadata["result_summary"] = data.summary
    metadata["result_diff"] = data.diff
    if data.error:
        metadata["result_error"] = data.error
    metadata["updated_at"] = datetime.utcnow().isoformat() + "Z"
    vault.write_file(task_path, metadata, body)

    # Notify delegating agent
    delegated_by = metadata.get("created_by", "")
    if delegated_by:
        delegating_agent = org.agent_registry.get(delegated_by)
        if delegating_agent and hasattr(delegating_agent, "vault"):
            today_str = str(date.today())
            status_word = "completed" if data.success else "failed"
            notif_path = f"inbox/{today_str}-task-{status_word}-{agent_id}.md"
            notif_meta = {
                "from": agent_id,
                "date": today_str,
                "type": f"task_{status_word}",
                "status": "pending",
                "task_ref": task_path,
            }
            notif_body = (
                f"## Task {status_word.title()}\n\n"
                f"**Task:** {metadata.get('name', task_path)}\n\n"
                f"**Summary:** {data.summary}\n\n"
            )
            if data.diff:
                notif_body += f"### Changes\n```\n{data.diff}\n```\n"
            if data.error:
                notif_body += f"### Error\n```\n{data.error}\n```\n"
            delegating_agent.vault.write_file(notif_path, notif_meta, notif_body)

    return {"status": metadata["status"], "task_path": task_path}


@org_router.post("/{agent_id}/activity")
async def update_activity(org_id: str, agent_id: str, data: ActivityUpdate):
    """Runner reports its current activity phase."""
    _, agent = _get_external_agent(org_id, agent_id)
    agent.current_activity = {
        "phase": data.phase,
        "task_name": data.task_name,
        "detail": data.detail,
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }
    return {"status": "ok"}


@org_router.get("/{agent_id}/tasks/{task_path:path}/status")
async def get_task_status(org_id: str, agent_id: str, task_path: str):
    """Runner polls this to check if a task has been approved/declined."""
    org, _ = _get_external_agent(org_id, agent_id)
    vault = _get_shared_vault(org)

    if not task_path.startswith("tasks/"):
        task_path = f"tasks/{task_path}"

    try:
        metadata, _ = vault.read_file(task_path)
    except FileNotFoundError:
        raise HTTPException(404, f"Task not found: {task_path}")

    return {"status": metadata.get("status", "unknown"), "task_path": task_path}

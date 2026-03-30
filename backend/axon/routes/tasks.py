"""Task management routes — list, create, update tasks in the shared vault."""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import axon.registry as registry

router = APIRouter()
org_router = APIRouter()


class TaskAttachment(BaseModel):
    type: str  # "vault_path", "url", "document"
    path: str
    label: str = ""


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    assignee: str = ""
    owner: str = ""
    priority: str = "p2"
    due_date: str = ""
    start_date: str = ""
    estimated_hours: float | None = None
    labels: list[str] = []
    parent_task: str = ""
    conversation_id: str = ""
    ws_target: str = ""


class TaskUpdate(BaseModel):
    status: str | None = None
    assignee: str | None = None
    priority: str | None = None
    name: str | None = None
    due_date: str | None = None
    start_date: str | None = None
    estimated_hours: float | None = None
    labels: list[str] | None = None
    body: str | None = None


class TaskRespond(BaseModel):
    content: str
    attachments: list[TaskAttachment] = []


# ── Shared helpers ────────────────────────────────────────────────────


def _get_shared_vault(org_id: str):
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Organization not found: {org_id}")
    if not org.shared_vault:
        raise HTTPException(404, f"No shared vault for org: {org_id}")
    return org.shared_vault


def _parse_tasks(vault) -> list[dict[str, Any]]:
    """Read all task files from the shared vault."""
    tasks_dir = Path(vault.vault_path) / "tasks"
    if not tasks_dir.exists():
        return []

    tasks = []
    for md_file in sorted(tasks_dir.glob("*.md"), reverse=True):
        if md_file.name.endswith("-index.md"):
            continue
        try:
            metadata, body = vault.read_file(f"tasks/{md_file.name}")
            metadata["path"] = f"tasks/{md_file.name}"
            metadata["body"] = body
            tasks.append(metadata)
        except Exception:
            continue
    return tasks


def _list_tasks(
    org_id: str,
    status: str | None,
    assignee: str | None,
    priority: str | None,
    conversation_id: str | None = None,
    ws_target: str | None = None,
):
    vault = _get_shared_vault(org_id)
    tasks = _parse_tasks(vault)

    if status:
        statuses = {s.strip() for s in status.split(",")}
        tasks = [t for t in tasks if t.get("status") in statuses]
    if assignee:
        tasks = [t for t in tasks if t.get("assignee") == assignee]
    if priority:
        tasks = [t for t in tasks if t.get("priority") == priority]
    if conversation_id:
        tasks = [t for t in tasks if t.get("conversation_id") == conversation_id]
    if ws_target:
        tasks = [t for t in tasks if t.get("ws_target") == ws_target]

    return tasks


def _get_task(org_id: str, task_path: str):
    vault = _get_shared_vault(org_id)
    try:
        metadata, body = vault.read_file(task_path)
        return {**metadata, "path": task_path, "body": body}
    except FileNotFoundError:
        raise HTTPException(404, f"Task not found: {task_path}")


def _create_task(org_id: str, data: TaskCreate):
    from axon.agents.shared_tools import SharedVaultToolExecutor, _slugify

    vault = _get_shared_vault(org_id)
    executor = SharedVaultToolExecutor(vault, "user")

    slug = _slugify(data.title)
    today_str = str(datetime.utcnow().date())
    path = f"tasks/{today_str}-{slug}.md"

    metadata = {
        "name": data.title,
        "type": "task",
        "owner": data.owner or "user",
        "assignee": data.assignee,
        "status": "pending",
        "priority": data.priority,
        "due_date": data.due_date,
        "start_date": data.start_date,
        "estimated_hours": data.estimated_hours,
        "parent_task": data.parent_task,
        "labels": data.labels,
        "conversation_id": data.conversation_id,
        "ws_target": data.ws_target,
        "created_by": "user",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "responses": [],
    }

    content = f"# {data.title}\n\n{data.description}"
    vault.write_file(path, metadata, content)
    vault._update_branch_index("tasks", slug, data.title)

    return {**metadata, "path": path, "body": content}


def _update_task(org_id: str, task_path: str, data: TaskUpdate):
    vault = _get_shared_vault(org_id)
    try:
        metadata, body = vault.read_file(task_path)
    except FileNotFoundError:
        raise HTTPException(404, f"Task not found: {task_path}")

    if data.status is not None:
        metadata["status"] = data.status
    if data.assignee is not None:
        metadata["assignee"] = data.assignee
    if data.priority is not None:
        metadata["priority"] = data.priority
    if data.name is not None:
        metadata["name"] = data.name
    if data.due_date is not None:
        metadata["due_date"] = data.due_date
    if data.start_date is not None:
        metadata["start_date"] = data.start_date
    if data.estimated_hours is not None:
        metadata["estimated_hours"] = data.estimated_hours
    if data.labels is not None:
        metadata["labels"] = data.labels
    if data.body is not None:
        body = data.body

    metadata["updated_at"] = datetime.utcnow().isoformat() + "Z"
    vault.write_file(task_path, metadata, body)

    return {**metadata, "path": task_path, "body": body}


def _respond_to_task(org_id: str, task_path: str, data: TaskRespond):
    vault = _get_shared_vault(org_id)
    try:
        metadata, body = vault.read_file(task_path)
    except FileNotFoundError:
        raise HTTPException(404, f"Task not found: {task_path}")

    response_entry = {
        "from": "user",
        "content": data.content,
        "attachments": [a.model_dump() for a in data.attachments],
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    if "responses" not in metadata:
        metadata["responses"] = []
    metadata["responses"].append(response_entry)
    metadata["updated_at"] = datetime.utcnow().isoformat() + "Z"
    vault.write_file(task_path, metadata, body)

    return {**metadata, "path": task_path, "body": body}


# ── Org-scoped routes ─────────────────────────────────────────────────


@org_router.get("")
async def list_tasks_org(
    org_id: str,
    status: str | None = None,
    assignee: str | None = None,
    priority: str | None = None,
    conversation_id: str | None = None,
    ws_target: str | None = None,
):
    return await asyncio.to_thread(
        _list_tasks, org_id, status, assignee, priority, conversation_id, ws_target,
    )


@org_router.get("/{task_path:path}")
async def get_task_org(org_id: str, task_path: str):
    if not task_path.startswith("tasks/"):
        task_path = f"tasks/{task_path}"
    return _get_task(org_id, task_path)


@org_router.post("")
async def create_task_org(org_id: str, data: TaskCreate):
    return _create_task(org_id, data)


@org_router.put("/{task_path:path}/respond")
async def respond_task_org(org_id: str, task_path: str, data: TaskRespond):
    if not task_path.startswith("tasks/"):
        task_path = f"tasks/{task_path}"
    return _respond_to_task(org_id, task_path, data)


@org_router.put("/{task_path:path}")
async def update_task_org(org_id: str, task_path: str, data: TaskUpdate):
    if not task_path.startswith("tasks/"):
        task_path = f"tasks/{task_path}"
    return _update_task(org_id, task_path, data)


# ── Legacy routes ─────────────────────────────────────────────────────


@router.get("")
async def list_tasks_legacy(
    status: str | None = None,
    assignee: str | None = None,
    priority: str | None = None,
    conversation_id: str | None = None,
    ws_target: str | None = None,
):
    return await asyncio.to_thread(
        _list_tasks, registry.default_org_id, status, assignee, priority, conversation_id, ws_target,
    )


@router.get("/{task_path:path}")
async def get_task_legacy(task_path: str):
    if not task_path.startswith("tasks/"):
        task_path = f"tasks/{task_path}"
    return _get_task(registry.default_org_id, task_path)


@router.post("")
async def create_task_legacy(data: TaskCreate):
    return _create_task(registry.default_org_id, data)


@router.put("/{task_path:path}/respond")
async def respond_task_legacy(task_path: str, data: TaskRespond):
    if not task_path.startswith("tasks/"):
        task_path = f"tasks/{task_path}"
    return _respond_to_task(registry.default_org_id, task_path, data)


@router.put("/{task_path:path}")
async def update_task_legacy(task_path: str, data: TaskUpdate):
    if not task_path.startswith("tasks/"):
        task_path = f"tasks/{task_path}"
    return _update_task(registry.default_org_id, task_path, data)

"""Approval routes — user approves or declines agent plans."""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import axon.registry as registry

org_router = APIRouter()


class DeclineRequest(BaseModel):
    reason: str = ""


def _get_shared_vault(org_id: str):
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Organization not found: {org_id}")
    if not org.shared_vault:
        raise HTTPException(404, f"No shared vault for org: {org_id}")
    return org


def _scan_pending(vault) -> list[dict[str, Any]]:
    """Scan task files for pending approvals (sync — runs in thread)."""
    tasks_dir = Path(vault.vault_path) / "tasks"
    if not tasks_dir.exists():
        return []

    pending = []
    for md_file in sorted(tasks_dir.glob("*.md"), reverse=True):
        if md_file.name.endswith("-index.md"):
            continue
        try:
            metadata, body = vault.read_file(f"tasks/{md_file.name}")
            if metadata.get("status") == "awaiting_approval":
                item = {
                    "task_path": f"tasks/{md_file.name}",
                    "title": metadata.get("name", ""),
                    "assignee": metadata.get("assignee", ""),
                    "delegated_by": metadata.get("created_by", ""),
                    "priority": metadata.get("priority", ""),
                    "plan_content": metadata.get("plan_content", ""),
                    "files_affected": metadata.get("files_affected", []),
                    "created_at": metadata.get("created_at", ""),
                    "updated_at": metadata.get("updated_at", ""),
                }
                task_type = metadata.get("type", "")
                if task_type:
                    item["type"] = task_type

                if task_type == "comms_outbound":
                    item["channel"] = metadata.get("channel", "")
                    item["comms_payload"] = metadata.get("comms_payload", "")
                elif task_type == "recruitment":
                    item["role"] = metadata.get("role", "")
                    item["agent_name"] = metadata.get("agent_name", "")
                    item["reason"] = metadata.get("reason", "")
                    item["requested_by"] = metadata.get("requested_by", "")
                    item["system_prompt"] = metadata.get("system_prompt", "")
                    item["domains"] = metadata.get("domains", [])
                    item["suggested_capabilities"] = metadata.get("suggested_capabilities", [])

                pending.append(item)
        except Exception:
            continue

    return pending


def _scan_history(
    vault, status: str, channel: str, limit: int,
) -> list[dict[str, Any]]:
    """Scan task files for approval history (sync — runs in thread)."""
    tasks_dir = Path(vault.vault_path) / "tasks"
    if not tasks_dir.exists():
        return []

    terminal_statuses = {"approved", "declined", "send_failed"}
    results: list[dict[str, Any]] = []

    for md_file in sorted(tasks_dir.glob("*.md"), reverse=True):
        if md_file.name.endswith("-index.md"):
            continue
        if len(results) >= limit:
            break
        try:
            metadata, body = vault.read_file(f"tasks/{md_file.name}")
        except Exception:
            continue

        file_status = metadata.get("status", "")
        if file_status not in terminal_statuses:
            continue
        if status and file_status != status:
            continue
        if channel and metadata.get("channel", "") != channel:
            continue

        item: dict[str, Any] = {
            "task_path": f"tasks/{md_file.name}",
            "title": metadata.get("name", ""),
            "status": file_status,
            "created_by": metadata.get("created_by", ""),
            "created_at": metadata.get("created_at", ""),
            "updated_at": metadata.get("updated_at", ""),
        }
        if metadata.get("type") == "comms_outbound":
            item["type"] = "comms_outbound"
            item["channel"] = metadata.get("channel", "")
            item["comms_payload"] = metadata.get("comms_payload", "")
            item["send_result"] = metadata.get("send_result", "")
        if file_status == "approved":
            item["approved_at"] = metadata.get("approved_at", "")
        if file_status == "declined":
            item["decline_reason"] = metadata.get("decline_reason", "")

        results.append(item)

    return results


@org_router.get("/pending")
async def list_pending_approvals(org_id: str):
    """Return all tasks awaiting user approval."""
    org = _get_shared_vault(org_id)
    return await asyncio.to_thread(_scan_pending, org.shared_vault)


@org_router.get("/history")
async def list_approval_history(
    org_id: str,
    status: str = "",
    channel: str = "",
    limit: int = 50,
):
    """Return past approvals (approved, declined, send_failed).

    Optional filters: ?status=approved&channel=email&limit=20
    """
    org = _get_shared_vault(org_id)
    return await asyncio.to_thread(
        _scan_history, org.shared_vault, status, channel, limit,
    )


@org_router.post("/{task_path:path}/approve")
async def approve_task(org_id: str, task_path: str):
    """Approve a task plan. Sets status to 'approved'.

    Recruitment tasks are detected automatically and delegated to the
    recruitment handler which scaffolds a vault and hot-loads the agent.
    """
    org = _get_shared_vault(org_id)
    vault = org.shared_vault

    if not task_path.startswith("tasks/"):
        task_path = f"tasks/{task_path}"

    try:
        metadata, body = vault.read_file(task_path)
    except FileNotFoundError:
        raise HTTPException(404, f"Task not found: {task_path}")

    if metadata.get("status") != "awaiting_approval":
        raise HTTPException(400, f"Task is not awaiting approval (status: {metadata.get('status')})")

    # Comms outbound tasks need the comms handler to actually send the message
    if metadata.get("type") == "comms_outbound":
        from axon.comms.approval_handler import handle_comms_approval
        return await handle_comms_approval(org, task_path, metadata, body)

    # Recruitment tasks need the specialized handler that actually creates the agent
    if metadata.get("type") == "recruitment":
        from axon.routes.recruitment import ApproveRequest, approve_recruitment

        # Use refined fields, fall back to role-based defaults
        agent_name = metadata.get("agent_name") or metadata.get("role", "New Agent")
        agent_id = agent_name.lower().replace(" ", "_").replace("-", "_")
        requested_by = metadata.get("requested_by", "")
        body_req = ApproveRequest(
            name=agent_name,
            agent_id=agent_id,
            title=metadata.get("agent_title") or metadata.get("role", ""),
            title_tag=metadata.get("agent_title_tag", ""),
            tagline=metadata.get("agent_tagline") or metadata.get("role", ""),
            color=metadata.get("agent_color", "#6B7280"),
            sparkle_color=metadata.get("agent_sparkle_color", "#9CA3AF"),
            parent_id=requested_by,
            system_prompt=metadata.get("system_prompt", ""),
            domains=metadata.get("domains", []),
        )
        return await approve_recruitment(org_id, task_path, body_req)

    metadata["status"] = "approved"
    metadata["approved_at"] = datetime.utcnow().isoformat() + "Z"
    metadata["updated_at"] = datetime.utcnow().isoformat() + "Z"
    vault.write_file(task_path, metadata, body)

    return {"status": "approved", "task_path": task_path}


@org_router.post("/{task_path:path}/decline")
async def decline_task(org_id: str, task_path: str, data: DeclineRequest | None = None):
    """Decline a task plan. Sets status to 'declined'."""
    org = _get_shared_vault(org_id)
    vault = org.shared_vault

    if not task_path.startswith("tasks/"):
        task_path = f"tasks/{task_path}"

    try:
        metadata, body = vault.read_file(task_path)
    except FileNotFoundError:
        raise HTTPException(404, f"Task not found: {task_path}")

    if metadata.get("status") != "awaiting_approval":
        raise HTTPException(400, f"Task is not awaiting approval (status: {metadata.get('status')})")

    metadata["status"] = "declined"
    if data and data.reason:
        metadata["decline_reason"] = data.reason
    metadata["updated_at"] = datetime.utcnow().isoformat() + "Z"
    vault.write_file(task_path, metadata, body)

    return {"status": "declined", "task_path": task_path}

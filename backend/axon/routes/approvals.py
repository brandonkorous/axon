"""Approval routes — user approves or declines agent plans."""

from __future__ import annotations

from datetime import date, datetime
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


@org_router.get("/pending")
async def list_pending_approvals(org_id: str):
    """Return all tasks awaiting user approval."""
    org = _get_shared_vault(org_id)
    vault = org.shared_vault

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
                # Include comms-specific fields for outbound message approvals
                if metadata.get("type") == "comms_outbound":
                    item["type"] = "comms_outbound"
                    item["channel"] = metadata.get("channel", "")
                    item["comms_payload"] = metadata.get("comms_payload", "")
                pending.append(item)
        except Exception:
            continue

    return pending


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

        role = metadata.get("role", "New Agent")
        agent_id = role.lower().replace(" ", "_")
        requested_by = metadata.get("requested_by", "")
        body_req = ApproveRequest(name=role, agent_id=agent_id, parent_id=requested_by)
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

    # Notify delegating agent
    delegated_by = metadata.get("created_by", "")
    if delegated_by:
        delegating_agent = org.agent_registry.get(delegated_by)
        if delegating_agent and hasattr(delegating_agent, "vault"):
            today_str = str(date.today())
            notif_path = f"inbox/{today_str}-plan-declined.md"
            notif_meta = {
                "from": "user",
                "date": today_str,
                "type": "plan_declined",
                "status": "pending",
                "task_ref": task_path,
            }
            reason_text = f"\n\n**Reason:** {data.reason}" if data and data.reason else ""
            notif_body = (
                f"## Plan Declined\n\n"
                f"**Task:** {metadata.get('name', task_path)}{reason_text}\n"
            )
            delegating_agent.vault.write_file(notif_path, notif_meta, notif_body)

    return {"status": "declined", "task_path": task_path}

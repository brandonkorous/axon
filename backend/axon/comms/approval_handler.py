"""Handle approved comms_outbound tasks — dispatch to senders."""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from axon.org import OrgInstance

logger = logging.getLogger(__name__)


async def handle_comms_approval(
    org: "OrgInstance",
    task_path: str,
    metadata: dict[str, Any],
    body: str,
) -> dict:
    """Called when a comms_outbound task is approved. Sends the message."""
    channel = metadata.get("channel", "")
    payload_raw = metadata.get("comms_payload", "{}")
    created_by = metadata.get("created_by", "")

    try:
        payload = json.loads(payload_raw)
    except json.JSONDecodeError:
        return {"status": "error", "detail": "Invalid comms_payload JSON"}

    # Resolve credentials and dispatch to the appropriate sender
    from axon.comms.credentials import resolve_credential

    # Resolve the from-name (email alias or agent_id) and display name
    from_name = created_by
    agent_display_name = ""
    if created_by:
        agent = org.agent_registry.get(created_by)
        if agent:
            agent_display_name = agent.name
            if hasattr(agent.config, "comms") and agent.config.comms.email_alias:
                from_name = agent.config.comms.email_alias

    result = ""
    if channel == "email":
        from axon.comms.senders import send_email
        api_key = await resolve_credential(org.id, "resend") or ""
        result = await send_email(
            api_key,
            org.config.comms.email_domain,
            to=payload.get("to", ""),
            subject=payload.get("subject", ""),
            body=payload.get("body", ""),
            cc=payload.get("cc", ""),
            from_name=from_name,
            signature=org.config.comms.email_signature,
            agent_display_name=agent_display_name,
        )
    elif channel == "discord":
        from axon.comms.senders import send_discord_message
        bot_token = await resolve_credential(org.id, "discord") or ""
        result = await send_discord_message(
            bot_token,
            target=payload.get("target", ""),
            content=payload.get("content", ""),
            is_dm=payload.get("is_dm", False),
        )
    else:
        return {"status": "error", "detail": f"Unknown comms channel: {channel}"}

    # Update task status
    vault = org.shared_vault
    now = datetime.utcnow().isoformat() + "Z"
    sent_ok = not result.startswith("Error")
    metadata["status"] = "approved" if sent_ok else "send_failed"
    metadata["approved_at"] = now
    metadata["updated_at"] = now
    metadata["send_result"] = result[:500]
    vault.write_file(task_path, metadata, body)

    # Notify the originating agent via inbox
    if created_by:
        agent = org.agent_registry.get(created_by)
        if agent and hasattr(agent, "vault"):
            today_str = str(date.today())
            status = "sent" if sent_ok else "failed"
            notif_path = f"inbox/{today_str}-comms-{status}.md"
            notif_meta = {
                "from": "system",
                "date": today_str,
                "type": f"comms_{status}",
                "status": "pending",
                "task_ref": task_path,
            }
            notif_body = f"## Message {status.title()}\n\n{result}"
            agent.vault.write_file(notif_path, notif_meta, notif_body)

    return {"status": "approved", "task_path": task_path, "sent": sent_ok, "result": result}

"""Web Push notification dispatch.

Sends push notifications via pywebpush when no browser tab is open
to receive WebSocket events.
"""

from __future__ import annotations

import asyncio
import json
import logging

from pywebpush import WebPushException, webpush

from axon.db.engine import _session_factory
from axon.db.crud.push import delete_subscription, get_all_subscriptions, get_or_create_vapid_keys

logger = logging.getLogger(__name__)

VAPID_CLAIMS = {"sub": "mailto:notifications@useaxon.dev"}

# Map event types to human-readable notification content
NOTIFICATION_MAP = {
    "task_done": {
        "title": "{agent_name} completed a task",
        "body": "{task_title}",
    },
    "task_failed": {
        "title": "{agent_name}: task failed",
        "body": "{task_title}",
    },
    "agent_result": {
        "title": "Result from {agent_name}",
        "body": "{task_title}",
    },
}


def build_notification_payload(
    event_type: str,
    *,
    agent_id: str,
    agent_name: str,
    task_title: str,
    org_id: str = "",
) -> dict:
    """Build a notification payload dict from an event."""
    template = NOTIFICATION_MAP.get(event_type, NOTIFICATION_MAP["agent_result"])
    title = template["title"].format(agent_name=agent_name, task_title=task_title)
    body = template["body"].format(agent_name=agent_name, task_title=task_title)
    url = f"/agent/{agent_id}" if agent_id else "/"

    return {
        "title": title,
        "body": body,
        "url": url,
        "tag": f"{agent_id}:{task_title[:50]}",
        "agent_id": agent_id,
    }


async def send_push_notification(
    title: str,
    body: str,
    url: str = "/",
    tag: str = "",
    agent_id: str = "",
) -> int:
    """Send a push notification to all subscribed browsers.

    Returns the number of notifications successfully sent.
    Automatically removes stale subscriptions (410 Gone).
    """
    async with _session_factory() as session:
        public_key, private_key = await get_or_create_vapid_keys(session)
        subscriptions = await get_all_subscriptions(session)

    if not subscriptions:
        return 0

    payload = json.dumps({
        "title": title,
        "body": body,
        "icon": "/favicon.svg",
        "tag": tag,
        "data": {"url": url, "agent_id": agent_id},
    })

    sent = 0
    stale_endpoints: list[str] = []

    for sub in subscriptions:
        subscription_info = {
            "endpoint": sub.endpoint,
            "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
        }
        try:
            await asyncio.to_thread(
                webpush,
                subscription_info=subscription_info,
                data=payload,
                vapid_private_key=private_key,
                vapid_claims=VAPID_CLAIMS,
            )
            sent += 1
        except WebPushException as e:
            if hasattr(e, "response") and e.response and e.response.status_code in (404, 410):
                stale_endpoints.append(sub.endpoint)
                logger.info("[PUSH] Removing stale subscription: %s", sub.endpoint[:60])
            else:
                logger.warning("[PUSH] Failed to send to %s: %s", sub.endpoint[:60], e)
        except Exception as e:
            logger.warning("[PUSH] Unexpected error for %s: %s", sub.endpoint[:60], e)

    # Clean up stale subscriptions
    if stale_endpoints:
        async with _session_factory() as session:
            for endpoint in stale_endpoints:
                await delete_subscription(session, endpoint)

    logger.info("[PUSH] Sent %d/%d notifications", sent, len(subscriptions))
    return sent


def fire_push_notification(
    event_type: str,
    *,
    agent_id: str,
    agent_name: str,
    task_title: str,
    org_id: str = "",
) -> None:
    """Build and send a push notification as a background task.

    Call this from the scheduler when ws_registry.push() returns 0 clients.
    """
    payload = build_notification_payload(
        event_type,
        agent_id=agent_id,
        agent_name=agent_name,
        task_title=task_title,
        org_id=org_id,
    )
    asyncio.create_task(send_push_notification(**payload))

"""Inbound email poller — polls Resend API for incoming emails and routes to agents."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import httpx

from axon.logging import get_logger
import axon.registry as registry

if TYPE_CHECKING:
    from axon.org import OrgInstance

logger = get_logger(__name__)

POLL_INTERVAL_SECONDS = 30


class InboundEmailPoller:
    """Background task that polls Resend for inbound emails.

    For each org with a Resend credential in the DB, polls the inbound
    emails endpoint and routes new emails to the appropriate agent
    based on the to-address pattern: {agent_id}@{email_domain}.
    """

    def __init__(self):
        self._task: asyncio.Task | None = None
        self._last_seen: dict[str, str] = {}  # org_id → last email id
        self._running = False

    async def start(self) -> None:
        """Start the polling loop as a background task."""
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("Inbound email poller started (interval: %ds)", POLL_INTERVAL_SECONDS)

    async def stop(self) -> None:
        """Cancel the polling task."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Inbound email poller stopped")

    async def _poll_loop(self) -> None:
        """Main polling loop — runs until cancelled."""
        while self._running:
            try:
                await self._poll_all_orgs()
            except Exception:
                logger.exception("Inbound email poll error")
            await asyncio.sleep(POLL_INTERVAL_SECONDS)

    async def _poll_all_orgs(self) -> None:
        """Poll inbound emails for every org with a Resend credential."""
        from axon.comms.credentials import resolve_credential

        for org_id, org in registry.org_registry.items():
            comms = org.config.comms
            if not comms.email_domain or not comms.inbound_polling:
                continue

            api_key = await resolve_credential(org_id, "resend")
            if not api_key:
                continue

            await self._poll_org(org_id, org, api_key, comms.email_domain)

    async def _poll_org(
        self, org_id: str, org: "OrgInstance", api_key: str, email_domain: str,
    ) -> None:
        """Poll and process inbound emails for a single org."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://api.resend.com/emails",
                    headers={"Authorization": f"Bearer {api_key}"},
                    params={"type": "inbound"},
                    timeout=15.0,
                )
            if resp.status_code != 200:
                logger.warning("Resend inbound API error for %s: %d", org_id, resp.status_code)
                return

            emails = resp.json().get("data", [])
        except Exception:
            logger.exception("Failed to fetch inbound emails for %s", org_id)
            return

        last_seen = self._last_seen.get(org_id, "")
        new_last_seen = last_seen

        for email in emails:
            email_id = email.get("id", "")
            if not email_id or email_id == last_seen:
                break  # Already processed

            if not new_last_seen:
                new_last_seen = email_id

            await self._route_email(org, email, email_domain)

        if new_last_seen:
            self._last_seen[org_id] = new_last_seen

    async def _route_email(
        self, org: "OrgInstance", email: dict, email_domain: str,
    ) -> None:
        """Route a single inbound email to the target agent."""
        to_addresses = email.get("to", [])
        from_addr = email.get("from", "unknown")
        subject = email.get("subject", "(no subject)")
        body = email.get("text", email.get("html", ""))

        for to_addr in to_addresses:
            if not to_addr.endswith(f"@{email_domain}"):
                continue

            agent_id = to_addr.split("@")[0]
            agent = org.agent_registry.get(agent_id)
            if not agent:
                logger.warning("Inbound email to unknown agent: %s", to_addr)
                continue

            # Inject as a message into the agent's conversation
            message = (
                f"[INBOUND EMAIL from {from_addr}]\n"
                f"Subject: {subject}\n\n"
                f"{body}"
            )

            try:
                async for _ in agent.process(message):
                    pass  # Consume the stream; response saved to conversation
                logger.info("Routed inbound email to %s from %s", agent_id, from_addr)
            except Exception:
                logger.exception("Failed to route email to agent %s", agent_id)

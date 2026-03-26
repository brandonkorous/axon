"""Global registry — org-scoped agent registries, breaks circular imports."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from axon.agents.agent import Agent
    from axon.agents.huddle import Huddle
    from axon.org import OrgInstance

# ── Org-scoped registry ─────────────────────────────────────────────

org_registry: dict[str, "OrgInstance"] = {}
"""All loaded organizations, keyed by org ID."""

default_org_id: str = ""
"""The currently active default org (used by legacy routes). Set during init_orgs()."""


# ── Legacy aliases (backward compat for Phase 1 transition) ────────
# These are populated during init_orgs() from the default org, so
# existing code that imports `agent_registry` or `huddle_instance`
# continues to work unchanged until routes are fully org-scoped.

agent_registry: dict[str, "Agent"] = {}
huddle_instance: "Huddle | None" = None


# ── Helpers ─────────────────────────────────────────────────────────


def get_org(org_id: str) -> "OrgInstance | None":
    """Get an organization by ID."""
    return org_registry.get(org_id)


def get_default_org() -> "OrgInstance | None":
    """Get the default organization."""
    return org_registry.get(default_org_id)


def get_agent(org_id: str, agent_id: str) -> "Agent | None":
    """Get an agent within an organization."""
    org = org_registry.get(org_id)
    if org is None:
        return None
    return org.agent_registry.get(agent_id)


def get_huddle(org_id: str) -> "Huddle | None":
    """Get the huddle for an organization."""
    org = org_registry.get(org_id)
    if org is None:
        return None
    return org.huddle


def list_orgs() -> list[dict]:
    """List all organizations as dicts."""
    return [
        {
            "id": org.config.id,
            "name": org.config.name,
            "description": org.config.description,
            "type": org.config.type,
            "comms": {
                "require_approval": org.config.comms.require_approval,
                "email_domain": org.config.comms.email_domain,
                "email_signature": org.config.comms.email_signature,
                "inbound_polling": org.config.comms.inbound_polling,
            },
            "agent_count": len(org.agent_registry),
            "has_huddle": org.huddle is not None,
        }
        for org in org_registry.values()
    ]

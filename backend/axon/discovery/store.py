"""Capability request store — persists gap requests to shared vault."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Any

from axon.discovery.models import CapabilityRequest, RequestStatus

logger = logging.getLogger(__name__)

# In-memory index of active requests (org_id → list of requests).
# Persisted to shared vault as capability-requests/*.json.
_REQUEST_CACHE: dict[str, list[CapabilityRequest]] = {}


def _vault_path(request_id: str) -> str:
    return f"capability-requests/{request_id}.json"


def create_request(
    *,
    agent_id: str,
    org_id: str,
    capability_type: str | None,
    capability_name: str,
    description: str,
    use_case: str,
    suggested_tools: list[str] | None = None,
    is_gap: bool = False,
    shared_vault: Any | None = None,
) -> CapabilityRequest:
    """Create and persist a new capability request."""
    request = CapabilityRequest(
        id=f"cap-{uuid.uuid4().hex[:12]}",
        agent_id=agent_id,
        org_id=org_id,
        capability_type=capability_type,
        capability_name=capability_name,
        description=description,
        use_case=use_case,
        suggested_tools=suggested_tools or [],
        is_gap=is_gap,
    )

    # Cache in memory
    _REQUEST_CACHE.setdefault(org_id, []).append(request)

    # Persist to shared vault if available
    if shared_vault:
        try:
            metadata = {
                "name": f"Capability request: {capability_name or description[:50]}",
                "description": f"{'Gap' if is_gap else 'Enable'} request from {agent_id}",
                "type": "capability-request",
                "status": "pending",
                "tags": "capability,request,gap" if is_gap else "capability,request",
            }
            shared_vault.write_file(
                _vault_path(request.id),
                metadata,
                request.model_dump_json(indent=2),
            )
        except Exception as e:
            logger.warning("Failed to persist capability request: %s", e)

    logger.info(
        "Capability request created: %s (agent=%s, gap=%s, name=%s)",
        request.id, agent_id, is_gap, capability_name or description[:40],
    )
    return request


def list_requests(
    org_id: str,
    *,
    status: RequestStatus | None = None,
    agent_id: str = "",
    gaps_only: bool = False,
) -> list[CapabilityRequest]:
    """List capability requests with optional filters."""
    requests = _REQUEST_CACHE.get(org_id, [])
    if status:
        requests = [r for r in requests if r.status == status]
    if agent_id:
        requests = [r for r in requests if r.agent_id == agent_id]
    if gaps_only:
        requests = [r for r in requests if r.is_gap]
    return sorted(requests, key=lambda r: r.timestamp, reverse=True)


def resolve_request(
    org_id: str,
    request_id: str,
    *,
    status: RequestStatus,
    resolved_by: str = "",
    note: str = "",
    shared_vault: Any | None = None,
) -> CapabilityRequest | None:
    """Update a request's status (approve, reject, mark as building, etc.)."""
    requests = _REQUEST_CACHE.get(org_id, [])
    for req in requests:
        if req.id == request_id:
            req.status = status
            req.resolved_by = resolved_by
            req.resolved_at = datetime.utcnow()
            req.resolution_note = note

            # Update in vault
            if shared_vault:
                try:
                    metadata = {
                        "name": f"Capability request: {req.capability_name or req.description[:50]}",
                        "description": f"Resolved: {status.value}",
                        "type": "capability-request",
                        "status": status.value,
                        "tags": "capability,request",
                    }
                    shared_vault.write_file(
                        _vault_path(req.id),
                        metadata,
                        req.model_dump_json(indent=2),
                    )
                except Exception as e:
                    logger.warning("Failed to update capability request in vault: %s", e)

            return req

    return None


def load_requests_from_vault(org_id: str, shared_vault: Any) -> None:
    """Hydrate the in-memory cache from shared vault on startup."""
    try:
        files = shared_vault.list_branch("capability-requests")
    except Exception:
        return

    loaded = 0
    for f in files:
        try:
            raw = shared_vault.read_file_raw(f"capability-requests/{f['name']}.json")
            # Strip frontmatter if present
            if raw.startswith("---"):
                parts = raw.split("---", 2)
                if len(parts) >= 3:
                    raw = parts[2].strip()
            req = CapabilityRequest.model_validate_json(raw)
            _REQUEST_CACHE.setdefault(org_id, []).append(req)
            loaded += 1
        except Exception as e:
            logger.debug("Skipping invalid request file %s: %s", f["name"], e)

    if loaded:
        logger.info("Loaded %d capability request(s) for org %s", loaded, org_id)

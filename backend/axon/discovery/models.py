"""Pydantic models for capability discovery and gap requests."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class CapabilityType(str, Enum):
    """Types of capabilities an agent can discover or request."""

    PLUGIN = "plugin"
    SKILL = "skill"
    INTEGRATION = "integration"
    SANDBOX = "sandbox"


class RequestStatus(str, Enum):
    """Lifecycle of a capability request."""

    PENDING = "pending"          # Awaiting human review
    APPROVED = "approved"        # Human approved, ready to enable/build
    BUILDING = "building"        # Builder agent is scaffolding it
    AVAILABLE = "available"      # Built and ready to enable
    ENABLED = "enabled"          # Auto-enabled for the requesting agent
    REJECTED = "rejected"        # Human declined the request


class CapabilityMatch(BaseModel):
    """A single result from searching existing registries."""

    type: CapabilityType
    name: str
    description: str
    category: str = ""
    triggers: list[str] = []
    is_enabled: bool = False     # Whether the requesting agent already has it
    requires_credentials: bool = False
    sandbox_type: str = ""       # For plugins that need a sandbox
    source: str = "builtin"


class CapabilityRequest(BaseModel):
    """A request for a capability — either existing or new (gap)."""

    id: str = Field(description="Unique request ID")
    agent_id: str = Field(description="Agent that made the request")
    org_id: str = Field(description="Organization context")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # What was requested
    capability_type: CapabilityType | None = None  # None for gap requests
    capability_name: str = ""     # Name if requesting existing capability
    description: str = ""         # Free-text description of what's needed
    use_case: str = ""            # Why the agent needs it
    suggested_tools: list[str] = []  # Agent's guess at tools it would need

    # Resolution
    status: RequestStatus = RequestStatus.PENDING
    is_gap: bool = False          # True if nothing in registry matched
    resolved_by: str = ""         # Who/what resolved it (human, builder agent)
    resolved_at: datetime | None = None
    resolution_note: str = ""

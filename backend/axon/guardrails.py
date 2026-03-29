"""Agent guardrails — per-agent boundary enforcement.

Configurable in agent.yaml under a `guardrails:` section:

    guardrails:
      tools:
        blocked: [comms_send_email]
      domains:
        allowed_domains: [marketing, branding]
        boundary_prompt: "Redirect legal questions to the appropriate specialist."
      actions:
        can_send: false
        require_approval: [task_create]
"""

from __future__ import annotations

from pydantic import BaseModel


class ToolRestriction(BaseModel):
    """Tool-level access control — whitelist or blacklist."""

    allowed: list[str] = []  # if non-empty, ONLY these tools are available
    blocked: list[str] = []  # these tools are removed from the agent's tool list


class DomainBoundary(BaseModel):
    """Domain-level advisory boundaries."""

    allowed_domains: list[str] = []  # e.g. ["marketing", "branding", "growth"]
    blocked_domains: list[str] = []  # e.g. ["legal", "compliance"]
    boundary_prompt: str = ""  # injected into system prompt


class ActionGate(BaseModel):
    """Action-level execution gates."""

    can_draft: bool = True  # can compose messages/documents
    can_execute: bool = True  # can execute tools in general
    can_send: bool = True  # can send comms (email, Discord, Slack, etc.)
    require_approval: list[str] = []  # tool names that need user approval before executing


class GuardrailsConfig(BaseModel):
    """Complete guardrails configuration for an agent."""

    tools: ToolRestriction = ToolRestriction()
    domains: DomainBoundary = DomainBoundary()
    actions: ActionGate = ActionGate()

    @property
    def has_tool_restrictions(self) -> bool:
        return bool(self.tools.allowed or self.tools.blocked)

    @property
    def has_domain_boundaries(self) -> bool:
        return bool(self.domains.allowed_domains or self.domains.blocked_domains or self.domains.boundary_prompt)

    @property
    def has_action_gates(self) -> bool:
        return bool(self.actions.require_approval) or not self.actions.can_send

    def filter_tools(self, tools: list[dict]) -> list[dict]:
        """Filter a tool list through allowed/blocked restrictions."""
        filtered = tools

        # Whitelist — only keep tools in the allowed list
        if self.tools.allowed:
            allowed = set(self.tools.allowed)
            filtered = [t for t in filtered if t["function"]["name"] in allowed]

        # Blacklist — remove blocked tools
        if self.tools.blocked:
            blocked = set(self.tools.blocked)
            filtered = [t for t in filtered if t["function"]["name"] not in blocked]

        # Action gate: block send tools if can_send is false
        if not self.actions.can_send:
            send_tools = {
                "comms_send_email", "comms_send_discord",
                "comms_send_slack", "comms_send_teams", "comms_send_zoom",
            }
            filtered = [t for t in filtered if t["function"]["name"] not in send_tools]

        return filtered

    def build_boundary_prompt(self) -> str:
        """Build system prompt instructions for domain boundaries."""
        parts: list[str] = []

        if self.domains.boundary_prompt:
            parts.append(self.domains.boundary_prompt)

        if self.domains.allowed_domains:
            domains = ", ".join(self.domains.allowed_domains)
            parts.append(
                f"Your advisory domain is limited to: **{domains}**. "
                "If a question falls outside your domain, acknowledge the question "
                "and redirect the user to the appropriate specialist."
            )

        if self.domains.blocked_domains:
            domains = ", ".join(self.domains.blocked_domains)
            parts.append(
                f"You must NOT advise on: **{domains}**. "
                "Redirect these topics to the appropriate specialist."
            )

        if self.actions.require_approval:
            tools = ", ".join(f"`{t}`" for t in self.actions.require_approval)
            parts.append(
                f"The following actions require user approval before execution: {tools}. "
                "Always confirm with the user before using them."
            )

        if not parts:
            return ""

        return "## Guardrails\n" + "\n".join(parts) + "\n"


class ConfidenceConfig(BaseModel):
    """Confidence gate configuration — tunable signal-to-noise."""

    mode: str = "balanced"  # high | balanced | exploration
    min_threshold: float = 0.0  # suppress outputs below this confidence
    tag_confidence: bool = False  # annotate outputs with confidence levels

    def build_confidence_prompt(self) -> str:
        """Build system prompt instructions for confidence mode."""
        if self.mode == "high":
            return (
                "## Confidence Mode: High\n"
                "Only state recommendations you are highly confident in. "
                "If you are uncertain, explicitly say so and explain what additional "
                "information would increase your confidence. Avoid speculative advice — "
                "the user relies on your signal quality.\n"
            )
        elif self.mode == "exploration":
            return (
                "## Confidence Mode: Exploration\n"
                "Surface all signals, including weak or speculative ones. "
                "Tag each recommendation with your confidence level "
                "(HIGH / MEDIUM / LOW). The user wants breadth of insight, "
                "not just high-confidence calls. Weak signals can be the most valuable.\n"
            )
        # balanced — no special instructions
        return ""

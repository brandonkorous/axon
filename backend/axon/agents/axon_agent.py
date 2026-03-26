"""Axon orchestrator agent — the primary assistant that routes to specialist agents."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, AsyncIterator

from axon.agents.agent import Agent, StreamChunk
from axon.config import PersonaConfig

if TYPE_CHECKING:
    from axon.audit import AuditLogger
    from axon.org import OrgCommsConfig
    from axon.usage import UsageTracker
    from axon.vault.vault import VaultManager


# Axon's routing system prompt — appended to its persona instructions
ROUTING_PROMPT = """
## Your Team

You have a team of specialist agents available. You can:
- Handle simple questions, status checks, and coordination directly
- Route to a specific agent when their expertise is needed
- Open a huddle when a topic warrants group discussion

When you decide to route to an agent, use the route_to_agent tool.
When you decide to start a huddle, use the open_huddle tool.

### Available Agents
{agent_roster}

### Routing Guidelines
- Technical architecture, infrastructure, vendor questions → route to the CTO advisor
- Strategy, fundraising, financials, hiring → route to the CEO advisor
- Marketing, BD, campaigns, GTM, partnerships → route to the COO advisor
- Topics touching multiple domains → start a huddle
- Simple coordination, scheduling, status → handle yourself
- If unsure, ask the user: "Would you like me to pull [agent] in on this?"
"""


ROUTING_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "route_to_agent",
            "description": "Route the user's message to a specialist agent. Use when the topic needs domain expertise.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "ID of the agent to route to",
                    },
                    "context": {
                        "type": "string",
                        "description": "Brief context for the agent about why they're being brought in",
                    },
                },
                "required": ["agent_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_huddle",
            "description": "Start a huddle for group discussion. Use when the topic warrants input from multiple advisors.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The topic for the huddle discussion",
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["standard", "vote", "devils_advocate", "pressure_test", "quick_take"],
                        "description": "Discussion mode",
                        "default": "standard",
                    },
                },
                "required": ["topic"],
            },
        },
    },
]


class AxonAgent(Agent):
    """The Axon orchestrator — routes to specialist agents or handles directly.

    Extends the base Agent with routing capabilities. When Axon decides
    to route to another agent, it yields a special StreamChunk with
    type="route" that the API layer uses to hand off to the target agent.
    """

    def __init__(
        self,
        config: PersonaConfig,
        available_agents: dict[str, PersonaConfig],
        data_dir: str = "/data",
        shared_vault: "VaultManager | None" = None,
        audit_logger: "AuditLogger | None" = None,
        usage_tracker: "UsageTracker | None" = None,
        org_id: str = "",
        org_comms_config: "OrgCommsConfig | None" = None,
    ):
        super().__init__(
            config, data_dir,
            shared_vault=shared_vault,
            audit_logger=audit_logger,
            usage_tracker=usage_tracker,
            org_id=org_id,
            org_comms_config=org_comms_config,
        )
        self.available_agents = available_agents
        self._update_system_prompt()

    def _update_system_prompt(self) -> None:
        """Inject the agent roster into the system prompt."""
        roster_lines = []
        for agent_id, agent_config in self.available_agents.items():
            if agent_id == self.id:
                continue  # Don't list self
            if agent_id == "huddle":
                continue  # Huddle is a mode, not a routable agent
            roster_lines.append(
                f"- **{agent_config.name}** (`{agent_id}`): {agent_config.title} — {agent_config.tagline}"
            )

        roster = "\n".join(roster_lines) if roster_lines else "No specialist agents configured."
        routing_section = ROUTING_PROMPT.format(agent_roster=roster)

        base_prompt = self.config.load_system_prompt(self.config.vault.path)
        self.system_prompt = f"{base_prompt}\n\n{routing_section}"

    def _build_tool_list(self) -> list:
        """Add routing tools to the standard vault tools."""
        tools = super()._build_tool_list()
        tools.extend(ROUTING_TOOLS)
        return tools

    async def _handle_tool_calls(
        self,
        messages: list[dict[str, Any]],
        tool_calls: dict[int, dict],
        response_so_far: str,
    ) -> AsyncIterator[StreamChunk]:
        """Override to intercept routing tool calls."""
        for tc_data in tool_calls.values():
            if tc_data["function"] == "route_to_agent":
                import json
                args = json.loads(tc_data["arguments"])
                yield StreamChunk(
                    agent_id=self.id,
                    type="route",
                    content=args.get("context", ""),
                    metadata={
                        "target_agent": args["agent_id"],
                        "context": args.get("context", ""),
                    },
                )
                return

            if tc_data["function"] == "open_huddle":
                import json
                args = json.loads(tc_data["arguments"])
                yield StreamChunk(
                    agent_id=self.id,
                    type="huddle",
                    content=args.get("topic", ""),
                    metadata={
                        "topic": args["topic"],
                        "mode": args.get("mode", "standard"),
                    },
                )
                return

        # For non-routing tools, use the parent handler
        async for chunk in super()._handle_tool_calls(messages, tool_calls, response_so_far):
            yield chunk

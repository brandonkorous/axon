"""DiscoveryToolExecutor — handles plugin discover/enable/request tool calls."""

from __future__ import annotations

import json
import logging
from typing import Any

from axon.discovery.models import CapabilityType
from axon.discovery.searcher import search_capabilities
from axon.discovery.store import create_request, list_requests

logger = logging.getLogger(__name__)


class DiscoveryToolExecutor:
    """Executes capability discovery and request tools for an agent."""

    def __init__(
        self,
        agent_id: str,
        org_id: str,
        *,
        get_config: Any = None,       # callable → PersonaConfig
        get_shared_vault: Any = None,  # callable → VaultManager | None
        on_capability_enabled: Any = None,  # callback after auto-enable
    ) -> None:
        self.agent_id = agent_id
        self.org_id = org_id
        self._get_config = get_config
        self._get_shared_vault = get_shared_vault
        self._on_capability_enabled = on_capability_enabled

    def can_handle(self, tool_name: str) -> bool:
        return tool_name in (
            "plugins_discover",
            "plugins_enable",
            "plugins_request",
        )

    async def execute(self, tool_name: str, arguments: str) -> str:
        try:
            args = json.loads(arguments) if arguments else {}
        except json.JSONDecodeError:
            return json.dumps({"error": f"Invalid JSON: {arguments}"})

        handlers = {
            "plugins_discover": self._discover,
            "plugins_enable": self._request_existing,
            "plugins_request": self._request_new,
        }

        handler = handlers.get(tool_name)
        if not handler:
            return json.dumps({"error": f"Unknown discovery tool: {tool_name}"})

        try:
            return await handler(args)
        except Exception as e:
            logger.exception("Discovery tool %s failed", tool_name)
            return json.dumps({"error": f"Discovery error: {e}"})

    async def _discover(self, args: dict) -> str:
        """Search across all registries for matching capabilities."""
        config = self._get_config() if self._get_config else None

        enabled_plugins = config.plugins.enabled if config else []
        enabled_skills = config.skills.enabled if config else []
        enabled_integrations = config.integrations.enabled if config else []

        matches = search_capabilities(
            query=args.get("query", ""),
            category=args.get("category", ""),
            cap_type=args.get("type", ""),
            enabled_plugins=enabled_plugins,
            enabled_skills=enabled_skills,
            enabled_integrations=enabled_integrations,
        )

        if not matches:
            return (
                "No plugins found matching your query. "
                "If you need something that doesn't exist yet, use "
                "plugins_request to describe what you need."
            )

        lines = [f"Found {len(matches)} matching capability(ies):\n"]
        for m in matches:
            status = "ENABLED" if m.is_enabled else "available"
            creds = " | requires credentials" if m.requires_credentials else ""
            sandbox = f" | sandbox: {m.sandbox_type}" if m.sandbox_type else ""
            triggers = f" | triggers: {', '.join(m.triggers[:5])}" if m.triggers else ""

            lines.append(
                f"- **{m.name}** [{m.type.value}] ({status}){creds}{sandbox}\n"
                f"  {m.description}{triggers}"
            )

        return "\n".join(lines)

    async def _request_existing(self, args: dict) -> str:
        """Request access to an existing capability."""
        cap_type = args.get("type", "")
        name = args.get("name", "")
        reason = args.get("reason", "")

        if not name:
            return json.dumps({"error": "name is required"})

        config = self._get_config() if self._get_config else None
        if not config:
            return json.dumps({"error": "Agent config not available"})

        # Check if already enabled
        already_enabled = (
            (cap_type == "plugin" and name in config.plugins.enabled)
            or (cap_type == "skill" and name in config.skills.enabled)
            or (cap_type == "integration" and name in config.integrations.enabled)
        )
        if already_enabled:
            return f"'{name}' is already enabled for you."

        # Check if it exists in the registry
        exists = False
        requires_creds = False

        if cap_type == "plugin":
            from axon.plugins.registry import PLUGIN_REGISTRY
            if name in PLUGIN_REGISTRY:
                exists = True
                instance = PLUGIN_REGISTRY[name]()
                requires_creds = bool(instance.manifest.required_credentials)

        elif cap_type == "skill":
            from axon.skills.registry import SKILL_REGISTRY
            exists = name in SKILL_REGISTRY

        elif cap_type == "integration":
            try:
                from axon.integrations.registry import INTEGRATION_REGISTRY
                exists = name in INTEGRATION_REGISTRY
                requires_creds = True  # Integrations always need creds
            except ImportError:
                pass

        if not exists:
            return (
                f"'{name}' not found in the {cap_type} registry. "
                "Use plugins_discover to search, or plugins_request "
                "if you need something that doesn't exist."
            )

        # Auto-enable if no credentials required
        if not requires_creds:
            return await self._auto_enable(cap_type, name, reason)

        # Credential-gated: create a pending request for human approval
        shared_vault = self._get_shared_vault() if self._get_shared_vault else None
        request = create_request(
            agent_id=self.agent_id,
            org_id=self.org_id,
            capability_type=cap_type,
            capability_name=name,
            description=f"Enable {cap_type} '{name}'",
            use_case=reason,
            shared_vault=shared_vault,
        )

        return (
            f"Request created ({request.id}): '{name}' requires credentials "
            "that must be configured by a human. Your request is pending approval. "
            "You'll gain access once credentials are set up."
        )

    async def _auto_enable(self, cap_type: str, name: str, reason: str) -> str:
        """Enable a capability immediately (no credentials needed)."""
        config = self._get_config() if self._get_config else None
        if not config:
            return json.dumps({"error": "Cannot access agent config"})

        if cap_type == "plugin":
            if name not in config.plugins.enabled:
                config.plugins.enabled.append(name)
        elif cap_type == "skill":
            if name not in config.skills.enabled:
                config.skills.enabled.append(name)
        elif cap_type == "integration":
            if name not in config.integrations.enabled:
                config.integrations.enabled.append(name)

        # Notify the agent to rebuild tools
        if self._on_capability_enabled:
            await self._on_capability_enabled(cap_type, name)

        logger.info(
            "Auto-enabled %s '%s' for agent %s (reason: %s)",
            cap_type, name, self.agent_id, reason,
        )

        return (
            f"Enabled {cap_type} '{name}' for you. "
            "Your tools have been updated — you can now use it."
        )

    async def _request_new(self, args: dict) -> str:
        """Request a capability that doesn't exist in any registry."""
        description = args.get("description", "")
        use_case = args.get("use_case", "")
        suggested_tools = args.get("suggested_tools", [])

        if not description:
            return json.dumps({"error": "description is required"})

        # Double-check nothing matches before creating a gap request
        matches = search_capabilities(query=description)
        if matches:
            top = matches[0]
            return (
                f"Before requesting something new — did you check '{top.name}' "
                f"({top.type.value})? It might cover your needs: {top.description}\n\n"
                "If it doesn't fit, call plugins_request again with a more "
                "specific description of what's missing."
            )

        shared_vault = self._get_shared_vault() if self._get_shared_vault else None
        request = create_request(
            agent_id=self.agent_id,
            org_id=self.org_id,
            capability_type=None,
            capability_name="",
            description=description,
            use_case=use_case,
            suggested_tools=suggested_tools,
            is_gap=True,
            shared_vault=shared_vault,
        )

        return (
            f"Gap request created ({request.id}): '{description[:80]}'\n"
            f"Use case: {use_case[:120]}\n"
            f"Suggested tools: {', '.join(suggested_tools) if suggested_tools else 'none'}\n\n"
            "This request is now visible to the organization. A human can approve it "
            "and a builder agent can scaffold it into a new plugin."
        )

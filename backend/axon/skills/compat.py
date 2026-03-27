"""Compatibility layer — wrap existing BaseIntegration as BaseSkill."""

from __future__ import annotations

from typing import Any

from axon.integrations.base import BaseIntegration
from axon.skills.base import BaseSkill
from axon.skills.manifest import SkillManifest


class IntegrationSkillAdapter(BaseSkill):
    """Wraps an existing BaseIntegration as a BaseSkill.

    This allows the integration registry to coexist with the
    skill registry during migration. Existing integrations
    continue to work unchanged while also appearing as skills.
    """

    def __init__(self, integration_cls: type[BaseIntegration]) -> None:
        self._integration_cls = integration_cls
        self._instance: BaseIntegration | None = None

        # Build manifest from integration class attributes
        proto = integration_cls()
        self.manifest = SkillManifest(
            name=proto.name or integration_cls.__name__.lower(),
            description=proto.description,
            tool_prefix=proto.tool_prefix,
            required_credentials=list(proto.required_scopes),
            auto_load=True,  # Integrations are always loaded when enabled
            category="integration",
        )
        super().__init__()

    def _ensure_instance(self) -> BaseIntegration:
        if not self._instance:
            self._instance = self._integration_cls()
            self._instance.configure(self._credentials)
        return self._instance

    def configure(self, credentials: dict[str, Any] | None = None) -> None:
        super().configure(credentials)
        if self._instance:
            self._instance.configure(self._credentials)

    def get_tools(self) -> list[dict[str, Any]]:
        return self._ensure_instance().get_tools()

    async def execute(self, tool_name: str, arguments: str) -> str:
        return await self._ensure_instance().execute(tool_name, arguments)

    async def on_agent_start(self, agent_id: str) -> None:
        await self._ensure_instance().on_agent_start(agent_id)

    async def on_agent_message(self, agent_id: str, message: str) -> str | None:
        return await self._ensure_instance().on_agent_message(agent_id, message)

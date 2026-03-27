"""Web research plugin — search and fetch web content."""

from __future__ import annotations

from typing import Any

from axon.plugins.base import BasePlugin
from axon.plugins.manifest import PluginManifest
from axon.web.tools import WEB_TOOLS


class WebResearchPlugin(BasePlugin):
    """Provides web_search and web_fetch tools as a plugin."""

    manifest = PluginManifest(
        name="web_research",
        version="1.0.0",
        description="Search the web and fetch page content for research",
        author="axon",
        tool_prefix="web_",
        tools=["web_search", "web_fetch"],
        auto_load=False,
        triggers=["search", "look up", "find information", "research", "what is", "google"],
        category="research",
        icon="search",
        python_deps=["trafilatura", "httpx"],
    )

    def get_tools(self) -> list[dict[str, Any]]:
        return list(WEB_TOOLS)

    async def execute(self, tool_name: str, arguments: str) -> str:
        # Delegate to existing WebToolExecutor
        from axon.web.executor import WebToolExecutor

        executor = WebToolExecutor()
        return await executor.execute(tool_name, arguments)

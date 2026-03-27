"""Web research plugin — wraps existing web_search and web_fetch tools."""

from axon.plugins.builtin.web_research.plugin import WebResearchPlugin
from axon.plugins.registry import register_plugin

register_plugin("web_research", WebResearchPlugin)

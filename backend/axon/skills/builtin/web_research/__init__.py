"""Web research skill — wraps existing web_search and web_fetch tools."""

from axon.skills.builtin.web_research.skill import WebResearchSkill
from axon.skills.registry import register_skill

register_skill("web_research", WebResearchSkill)

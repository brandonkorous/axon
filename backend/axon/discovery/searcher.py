"""Cross-registry capability search — plugins, skills, integrations, sandboxes."""

from __future__ import annotations

import logging
from typing import Any

from axon.discovery.models import CapabilityMatch, CapabilityType

logger = logging.getLogger(__name__)


def search_capabilities(
    query: str,
    *,
    category: str = "",
    cap_type: str = "",
    enabled_plugins: list[str] | None = None,
    enabled_skills: list[str] | None = None,
    enabled_integrations: list[str] | None = None,
) -> list[CapabilityMatch]:
    """Search across all registries for capabilities matching a query.

    Uses simple token matching — no LLM needed. Scores results by
    relevance (trigger match > name match > description match).
    """
    enabled_plugins = enabled_plugins or []
    enabled_skills = enabled_skills or []
    enabled_integrations = enabled_integrations or []

    tokens = [t.lower() for t in query.split() if len(t) > 1]
    if not tokens:
        return []

    results: list[tuple[float, CapabilityMatch]] = []

    # Filter by type if specified
    search_plugins = not cap_type or cap_type == "plugin"
    search_skills = not cap_type or cap_type == "skill"
    search_integrations = not cap_type or cap_type == "integration"
    search_sandboxes = not cap_type or cap_type == "sandbox"

    if search_plugins:
        results.extend(_search_plugins(tokens, category, enabled_plugins))

    if search_skills:
        results.extend(_search_skills(tokens, category, enabled_skills))

    if search_integrations:
        results.extend(_search_integrations(tokens, category, enabled_integrations))

    if search_sandboxes:
        results.extend(_search_sandboxes(tokens))

    # Sort by relevance score descending
    results.sort(key=lambda x: x[0], reverse=True)
    return [match for _, match in results[:15]]


def _score_tokens(tokens: list[str], fields: dict[str, float]) -> float:
    """Score how well tokens match weighted text fields.

    fields: {text_content: weight} — higher weight = more important match.
    """
    score = 0.0
    for text, weight in fields.items():
        lower = text.lower()
        for token in tokens:
            if token in lower:
                score += weight
    return score


def _search_plugins(
    tokens: list[str], category: str, enabled: list[str],
) -> list[tuple[float, CapabilityMatch]]:
    """Search the plugin registry."""
    from axon.plugins.registry import PLUGIN_REGISTRY, PLUGIN_SOURCE

    results: list[tuple[float, CapabilityMatch]] = []
    for name, cls in PLUGIN_REGISTRY.items():
        instance = cls()
        m = instance.manifest

        if category and m.category != category:
            continue

        trigger_text = " ".join(m.triggers)
        score = _score_tokens(tokens, {
            m.name: 3.0,
            trigger_text: 2.5,
            m.description: 1.0,
            m.category: 0.5,
        })

        if score > 0:
            results.append((score, CapabilityMatch(
                type=CapabilityType.PLUGIN,
                name=m.name,
                description=m.description,
                category=m.category,
                triggers=m.triggers,
                is_enabled=name in enabled,
                requires_credentials=bool(m.required_credentials),
                sandbox_type=m.sandbox_type,
                source=PLUGIN_SOURCE.get(name, "builtin"),
            )))

    return results


def _search_skills(
    tokens: list[str], category: str, enabled: list[str],
) -> list[tuple[float, CapabilityMatch]]:
    """Search the skill registry."""
    from axon.skills.registry import SKILL_REGISTRY, SKILL_SOURCE

    results: list[tuple[float, CapabilityMatch]] = []
    for name, defn in SKILL_REGISTRY.items():
        if category and defn.category != category:
            continue

        trigger_text = " ".join(defn.triggers)
        score = _score_tokens(tokens, {
            defn.name: 3.0,
            trigger_text: 2.5,
            defn.description: 1.0,
            defn.category: 0.5,
        })

        if score > 0:
            results.append((score, CapabilityMatch(
                type=CapabilityType.SKILL,
                name=defn.name,
                description=defn.description,
                category=defn.category,
                triggers=defn.triggers,
                is_enabled=name in enabled,
                source=SKILL_SOURCE.get(name, "builtin"),
            )))

    return results


def _search_integrations(
    tokens: list[str], category: str, enabled: list[str],
) -> list[tuple[float, CapabilityMatch]]:
    """Search the integration registry."""
    try:
        from axon.integrations.registry import INTEGRATION_REGISTRY
    except ImportError:
        return []

    results: list[tuple[float, CapabilityMatch]] = []
    for name, cls in INTEGRATION_REGISTRY.items():
        instance = cls()
        desc = getattr(instance, "description", "")

        score = _score_tokens(tokens, {
            name: 3.0,
            desc: 1.0,
        })

        if score > 0:
            results.append((score, CapabilityMatch(
                type=CapabilityType.INTEGRATION,
                name=name,
                description=desc,
                is_enabled=name in enabled,
                requires_credentials=True,  # Integrations always need creds
                source="integration",
            )))

    return results


def _search_sandboxes(tokens: list[str]) -> list[tuple[float, CapabilityMatch]]:
    """Search available sandbox types."""
    from axon.sandbox.types import SANDBOX_METADATA, SandboxType

    results: list[tuple[float, CapabilityMatch]] = []
    for stype in SandboxType:
        meta = SANDBOX_METADATA.get(stype, {})
        desc = meta.get("description", "")
        score = _score_tokens(tokens, {
            stype.value: 3.0,
            desc: 1.5,
        })

        if score > 0:
            results.append((score, CapabilityMatch(
                type=CapabilityType.SANDBOX,
                name=stype.value,
                description=desc,
                category="sandbox",
                source="builtin",
            )))

    return results

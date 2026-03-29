"""Pattern resolver — selects and assembles patterns for agent prompts."""

from __future__ import annotations

from axon.patterns.models import CognitivePattern
from axon.patterns.registry import (
    PATTERN_METHODOLOGY,
    PATTERN_REGISTRY,
    get_patterns_for_role,
)

# Map common agent titles to role keys
_TITLE_TO_ROLE: dict[str, str] = {
    "ceo": "ceo",
    "chief executive": "ceo",
    "cto": "cto",
    "chief technology": "cto",
    "coo": "coo",
    "chief operating": "coo",
    "cmo": "cmo",
    "chief marketing": "cmo",
    "chief community": "cmo",  # closest match
    "cfo": "coo",  # closest match for ops/finance
    "chief financial": "coo",
    "chief legal": "coo",
    "designer": "designer",
    "design": "designer",
    "developer": "engineer",
    "engineer": "engineer",
    "engineering": "engineer",
}


def _detect_role(title: str) -> str:
    """Detect the pattern role from an agent's title."""
    title_lower = title.lower()
    for keyword, role in _TITLE_TO_ROLE.items():
        if keyword in title_lower:
            return role
    return ""


def resolve_patterns_for_agent(
    title: str,
    explicit_patterns: list[str] | None = None,
) -> list[CognitivePattern]:
    """Resolve which patterns to inject for an agent.

    If explicit_patterns is provided, use those. Otherwise auto-match by title.
    """
    if explicit_patterns:
        return [
            PATTERN_REGISTRY[name]
            for name in explicit_patterns
            if name in PATTERN_REGISTRY
        ]

    role = _detect_role(title)
    if not role:
        return []
    return get_patterns_for_role(role)


def build_pattern_prompt(patterns: list[CognitivePattern]) -> str:
    """Build the prompt fragment for active cognitive patterns."""
    if not patterns:
        return ""

    sections: list[str] = []
    for pattern in patterns:
        methodology = PATTERN_METHODOLOGY.get(pattern.name, "")
        if not methodology:
            continue
        attribution = f" ({pattern.attribution})" if pattern.attribution else ""
        display = pattern.display_name or pattern.name.replace("_", " ").title()
        sections.append(f"### {display}{attribution}\n\n{methodology}")

    if not sections:
        return ""

    return "## Cognitive Patterns\n\n" + "\n\n".join(sections)

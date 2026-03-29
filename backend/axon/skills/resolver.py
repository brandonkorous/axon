"""Cognitive skill resolver — selects and assembles skills for agent prompts."""

from __future__ import annotations

from axon.skills.registry import SKILL_REGISTRY, SKILL_METHODOLOGY, get_skill
from axon.structured_output import OutputField, build_output_instructions


def resolve_skills_for_message(message: str, enabled_skills: list[str]) -> list[str]:
    """Return skill names to activate for the given message.

    - Skills with auto_inject=True are always included (if enabled).
    - Others are included if any of their triggers appear in the message.
    """
    message_lower = message.lower()
    active: list[str] = []

    for name in enabled_skills:
        defn = get_skill(name)
        if not defn:
            continue

        if defn.auto_inject:
            active.append(name)
            continue

        # Check trigger keywords
        for trigger in defn.triggers:
            if trigger.lower() in message_lower:
                active.append(name)
                break

    return active


def get_active_output_fields(skill_names: list[str]) -> list[OutputField]:
    """Collect output fields from all active skills."""
    fields: list[OutputField] = []
    seen: set[str] = set()
    for name in skill_names:
        defn = SKILL_REGISTRY.get(name)
        if not defn or not defn.outputs:
            continue
        for f in defn.outputs:
            if f.name not in seen:
                fields.append(f)
                seen.add(f.name)
    return fields


def build_skill_prompt(skill_names: list[str]) -> str:
    """Build the combined prompt fragment for active skills.

    Returns empty string if no skills are active.  Appends structured
    output instructions if any active skill defines output fields.
    """
    if not skill_names:
        return ""

    sections: list[str] = []
    for name in skill_names:
        defn = SKILL_REGISTRY.get(name)
        methodology = SKILL_METHODOLOGY.get(name, "")
        if not defn or not methodology:
            continue

        # Convert snake_case name to Title Case for display
        display_name = defn.name.replace("_", " ").title()
        sections.append(f"### {display_name}\n\n{methodology}")

    if not sections:
        return ""

    prompt = "## Active Skills\n\n" + "\n\n".join(sections)

    # Append structured output instructions if any skill defines outputs
    output_fields = get_active_output_fields(skill_names)
    if output_fields:
        prompt += build_output_instructions(output_fields)

    return prompt

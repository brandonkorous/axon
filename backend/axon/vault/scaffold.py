"""Vault scaffolding — initialize new vaults from templates."""

from __future__ import annotations

import shutil
from pathlib import Path


TEMPLATES_DIR = Path(__file__).parent.parent / "vault_templates"


def scaffold_vault(
    vault_path: str | Path,
    template: str = "advisor",
    agent_name: str = "Agent",
    agent_title: str = "",
    agent_id: str = "",
    agent_tagline: str = "",
) -> Path:
    """Initialize a new vault from a template.

    Args:
        vault_path: Where to create the vault.
        template: Template name (advisor, orchestrator, executor).
        agent_name: Agent's name for placeholder replacement.
        agent_title: Agent's title for placeholder replacement.
        agent_id: Agent's unique ID for config placeholder replacement.
        agent_tagline: Agent's tagline for config placeholder replacement.

    Returns:
        Path to the created vault.
    """
    vault = Path(vault_path)
    template_dir = TEMPLATES_DIR / template

    if not template_dir.exists():
        raise FileNotFoundError(f"Template not found: {template}")

    if vault.exists() and any(vault.iterdir()):
        raise FileExistsError(f"Vault already exists and is not empty: {vault}")

    # Derive defaults from agent_name if not provided
    if not agent_id:
        agent_id = agent_name.lower().replace(" ", "_")
    if not agent_tagline:
        agent_tagline = agent_title or agent_name

    # Copy template to vault
    vault.mkdir(parents=True, exist_ok=True)
    for item in template_dir.rglob("*"):
        relative = item.relative_to(template_dir)
        target = vault / relative

        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            content = item.read_text(encoding="utf-8")
            # Replace placeholders — escape backslashes for YAML safety
            replacements = {
                "{{AGENT_NAME}}": agent_name,
                "{{AGENT_TITLE}}": agent_title,
                "{{AGENT_ID}}": agent_id,
                "{{AGENT_TAGLINE}}": agent_tagline,
            }
            for placeholder, value in replacements.items():
                safe_value = value.replace("\\", "/")
                content = content.replace(placeholder, safe_value)
            target.write_text(content, encoding="utf-8")

    return vault


def list_templates() -> list[str]:
    """List available vault templates."""
    if not TEMPLATES_DIR.exists():
        return []
    return [d.name for d in TEMPLATES_DIR.iterdir() if d.is_dir()]

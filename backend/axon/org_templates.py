"""Org templates — curated agent sets for different use cases."""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml


TEMPLATES_DIR = Path(__file__).parent / "org_templates"
BASE_DIR = TEMPLATES_DIR / "_base"

# Human-readable metadata for each template type
TEMPLATE_META = {
    "startup": {
        "name": "Startup",
        "description": "AI advisory board for founders — strategy, technical, and operations advisors.",
        "icon": "rocket",
    },
    "family": {
        "name": "Family",
        "description": "Family assistant — organizer, researcher, wellness coach, and budget advisor.",
        "icon": "home",
    },
    "job-hunt": {
        "name": "Job Hunt",
        "description": "Career strategy team — resume specialist, interview coach, and career advisor.",
        "icon": "briefcase",
    },
    "creator": {
        "name": "Creator",
        "description": "Creative team — content strategist, editor, and business advisor.",
        "icon": "palette",
    },
    "student": {
        "name": "Student",
        "description": "Study team — subject tutor, academic planner, and career mentor.",
        "icon": "graduation-cap",
    },
}


def list_templates() -> list[dict]:
    """List all available org templates with their agents."""
    templates = []
    for template_dir in sorted(TEMPLATES_DIR.iterdir()):
        if not template_dir.is_dir() or template_dir.name.startswith("_"):
            continue
        template = _load_template_info(template_dir)
        if template:
            templates.append(template)
    return templates


def get_template(template_id: str) -> dict | None:
    """Get detailed info for a specific template."""
    template_dir = TEMPLATES_DIR / template_id
    if not template_dir.is_dir():
        return None
    return _load_template_info(template_dir)


def scaffold_from_template(
    orgs_dir: Path,
    org_id: str,
    template_id: str,
    org_name: str,
) -> Path:
    """Scaffold a new org from a template.

    1. Create org directory structure via scaffold_org()
    2. Copy base vaults (axon)
    3. Copy template-specific advisor vaults
    4. Generate huddle vault with correct advisor mounts and roster
    5. Write org.yaml with type field
    """
    from axon.org import scaffold_org

    template_dir = TEMPLATES_DIR / template_id
    if not template_dir.is_dir():
        raise ValueError(f"Unknown template: {template_id}")

    org_path = orgs_dir / org_id

    # Step 1: Scaffold base org structure (shared vault, data dirs, etc.)
    scaffold_org(org_path, org_name=org_name)

    vaults_dest = org_path / "vaults"

    # Step 2: Copy base vaults (axon — huddle handled separately)
    if BASE_DIR.exists():
        _copy_vault_templates(
            BASE_DIR / "vaults", vaults_dest, org_name,
            exclude=["huddle"],
        )

    # Step 3: Copy template-specific advisor vaults
    template_vaults_dir = template_dir / "vaults"
    advisor_ids: list[str] = []
    if template_vaults_dir.exists():
        advisor_ids = _copy_vault_templates(
            template_vaults_dir, vaults_dest, org_name,
        )

    # Step 4: Generate huddle vault with advisor mounts and roster
    _generate_huddle_vault(vaults_dest, template_vaults_dir, advisor_ids)

    # Step 5: Write org.yaml with type
    org_yaml = org_path / "org.yaml"
    org_config = {
        "id": org_id,
        "name": org_name,
        "type": template_id,
        "description": TEMPLATE_META.get(template_id, {}).get(
            "description", f"Organization created from {template_id} template"
        ),
    }
    with open(org_yaml, "w", encoding="utf-8") as f:
        yaml.dump(org_config, f, default_flow_style=False, sort_keys=False)

    return org_path


def _load_template_info(template_dir: Path) -> dict | None:
    """Load template metadata and agent list from a template directory."""
    template_id = template_dir.name
    meta = TEMPLATE_META.get(template_id, {})

    org_yaml = template_dir / "org.yaml"
    if not org_yaml.exists():
        return None

    # Discover agents from vaults/*/agent.yaml
    agents = []
    vaults_dir = template_dir / "vaults"
    if vaults_dir.exists():
        for vault_dir in sorted(vaults_dir.iterdir()):
            agent_yaml = vault_dir / "agent.yaml"
            if not vault_dir.is_dir() or not agent_yaml.exists():
                continue
            with open(agent_yaml, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            agents.append({
                "id": data.get("id", vault_dir.name),
                "name": data.get("name", vault_dir.name.title()),
                "title": data.get("title", ""),
                "tagline": data.get("tagline", ""),
                "color": data.get("ui", {}).get("color", "#6B7280"),
            })

    return {
        "id": template_id,
        "name": meta.get("name", template_id.title()),
        "description": meta.get("description", ""),
        "icon": meta.get("icon", ""),
        "agents": agents,
    }


def _copy_vault_templates(
    src_vaults: Path,
    dest_vaults: Path,
    org_name: str,
    exclude: list[str] | None = None,
) -> list[str]:
    """Copy vault directories from template to org, return list of agent IDs."""
    agent_ids = []
    exclude = exclude or []

    if not src_vaults.exists():
        return agent_ids

    for vault_dir in sorted(src_vaults.iterdir()):
        if not vault_dir.is_dir() or vault_dir.name in exclude:
            continue

        agent_yaml = vault_dir / "agent.yaml"
        if not agent_yaml.exists():
            continue

        dest = dest_vaults / vault_dir.name
        if (dest / "agent.yaml").exists():
            continue  # Never overwrite fully initialized vaults

        # Copy entire vault directory with placeholder replacement
        dest.mkdir(parents=True, exist_ok=True)
        for item in vault_dir.rglob("*"):
            if item.is_dir():
                continue
            relative = item.relative_to(vault_dir)
            target = dest / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            content = item.read_text(encoding="utf-8")
            content = content.replace("{{ORG_NAME}}", org_name)
            target.write_text(content, encoding="utf-8")

        # Read agent ID from the copied config
        with open(agent_yaml, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        agent_ids.append(data.get("id", vault_dir.name))

    return agent_ids


def _generate_huddle_vault(
    vaults_dest: Path,
    template_vaults_dir: Path,
    advisor_ids: list[str],
) -> None:
    """Generate the huddle vault with advisor mounts and roster instructions."""
    huddle_dest = vaults_dest / "huddle"
    huddle_dest.mkdir(parents=True, exist_ok=True)

    # Build read_only_mounts for advisor vaults
    mounts = [
        {"path": f"/vaults/{aid}", "root_file": "second-brain.md"}
        for aid in advisor_ids
    ]

    # Load base huddle agent.yaml template and replace mounts placeholder
    base_huddle_yaml = BASE_DIR / "vaults" / "huddle" / "agent.yaml"
    if base_huddle_yaml.exists():
        content = base_huddle_yaml.read_text(encoding="utf-8")
        # The template has {{ADVISOR_MOUNTS}} as a YAML placeholder —
        # replace it with the actual mounts list
        mounts_yaml = yaml.dump(mounts, default_flow_style=False).strip()
        content = content.replace("'{{ADVISOR_MOUNTS}}'", mounts_yaml)
        content = content.replace("{{ADVISOR_MOUNTS}}", mounts_yaml)
        (huddle_dest / "agent.yaml").write_text(content, encoding="utf-8")
    else:
        # Generate from scratch
        huddle_config = {
            "id": "huddle",
            "name": "The Huddle",
            "title": "Advisory Group Session",
            "tagline": "Where your team debates, disagrees, and converges",
            "type": "huddle",
            "model": {"max_tokens": 8192, "temperature": 0.8},
            "vault": {
                "root_file": "second-brain.md",
                "read_only_mounts": mounts,
                "writable_paths": ["."],
            },
            "memory": {"max_context_tokens": 6000},
            "delegation": {"can_delegate_to": [], "accepts_from": ["axon"]},
            "behavior": {"auto_save": True, "first_message": True},
            "ui": {"color": "#F59E0B", "sparkle_color": "#FBBF24"},
        }
        with open(huddle_dest / "agent.yaml", "w", encoding="utf-8") as f:
            yaml.dump(huddle_config, f, default_flow_style=False, sort_keys=False)

    # Build advisor roster for instructions
    roster_lines = []
    for aid in advisor_ids:
        agent_yaml = template_vaults_dir / aid / "agent.yaml"
        if agent_yaml.exists():
            with open(agent_yaml, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            name = data.get("name", aid.title())
            title = data.get("title", "")
            tagline = data.get("tagline", "")
            roster_lines.append(f"### {name} — {title} (\"{tagline}\")")
        else:
            roster_lines.append(f"### {aid.title()}")

    roster = "\n\n".join(roster_lines)

    # Load base huddle instructions template and replace roster placeholder
    base_instructions = BASE_DIR / "vaults" / "huddle" / "instructions.md"
    if base_instructions.exists():
        content = base_instructions.read_text(encoding="utf-8")
        content = content.replace("{{ADVISOR_ROSTER}}", roster)
    else:
        content = f"# The Huddle\n\n## The Advisors\n\n{roster}\n"

    (huddle_dest / "instructions.md").write_text(content, encoding="utf-8")

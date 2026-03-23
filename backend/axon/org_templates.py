"""Org templates — curated persona sets for different use cases."""

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
    """List all available org templates with their personas."""
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
    2. Copy base personas (axon + huddle)
    3. Copy template-specific personas
    4. Generate huddle config with correct advisor mounts
    5. Generate huddle instructions with advisor roster
    6. Write org.yaml with type field
    """
    from axon.org import scaffold_org

    template_dir = TEMPLATES_DIR / template_id
    if not template_dir.is_dir():
        raise ValueError(f"Unknown template: {template_id}")

    org_path = orgs_dir / org_id

    # Step 1: Scaffold base org structure (shared vault, data dirs, etc.)
    scaffold_org(org_path, org_name=org_name)

    personas_dest = org_path / "personas"
    prompts_dest = personas_dest / "prompts"
    prompts_dest.mkdir(parents=True, exist_ok=True)

    # Step 2: Copy base personas (axon)
    if BASE_DIR.exists():
        _copy_persona_files(BASE_DIR / "personas", personas_dest, org_name, exclude=["huddle"])

    # Step 3: Copy template-specific personas
    template_personas_dir = template_dir / "personas"
    advisor_ids: list[str] = []
    if template_personas_dir.exists():
        advisor_ids = _copy_persona_files(template_personas_dir, personas_dest, org_name)

    # Step 4: Generate huddle config with advisor vault mounts
    _generate_huddle_config(personas_dest, advisor_ids)

    # Step 5: Generate huddle instructions with advisor roster
    _generate_huddle_instructions(personas_dest, template_personas_dir, advisor_ids)

    # Step 6: Create per-advisor vault directories
    vaults_dir = org_path / "vaults"
    for advisor_id in advisor_ids:
        vault_path = vaults_dir / advisor_id
        vault_path.mkdir(parents=True, exist_ok=True)
        root_file = vault_path / "second-brain.md"
        if not root_file.exists():
            root_file.write_text(
                f"# {advisor_id.title()} Vault\n\nPersistent memory for {advisor_id}.\n",
                encoding="utf-8",
            )
    # Also create axon and huddle vaults
    for name in ("axon", "huddle"):
        vault_path = vaults_dir / name
        vault_path.mkdir(parents=True, exist_ok=True)
        root_file = vault_path / "second-brain.md"
        if not root_file.exists():
            root_file.write_text(
                f"# {name.title()} Vault\n\nPersistent memory for {name}.\n",
                encoding="utf-8",
            )

    # Step 7: Write org.yaml with type
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
    """Load template metadata and persona list from a template directory."""
    template_id = template_dir.name
    meta = TEMPLATE_META.get(template_id, {})

    # Load org.yaml for type info
    org_yaml = template_dir / "org.yaml"
    if not org_yaml.exists():
        return None

    # Discover personas
    personas = []
    personas_dir = template_dir / "personas"
    if personas_dir.exists():
        for yaml_file in sorted(personas_dir.glob("*.yaml")):
            if yaml_file.name.startswith("_"):
                continue
            with open(yaml_file, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            personas.append({
                "id": data.get("id", yaml_file.stem),
                "name": data.get("name", yaml_file.stem.title()),
                "title": data.get("title", ""),
                "tagline": data.get("tagline", ""),
                "color": data.get("ui", {}).get("color", "#6B7280"),
            })

    return {
        "id": template_id,
        "name": meta.get("name", template_id.title()),
        "description": meta.get("description", ""),
        "icon": meta.get("icon", ""),
        "personas": personas,
    }


def _copy_persona_files(
    src_dir: Path,
    dest_dir: Path,
    org_name: str,
    exclude: list[str] | None = None,
) -> list[str]:
    """Copy persona YAML and instruction files, return list of persona IDs."""
    persona_ids = []
    exclude = exclude or []

    for item in src_dir.iterdir():
        stem = item.stem
        if stem.startswith("_"):
            continue

        # Skip excluded personas
        if any(stem == ex or stem.startswith(f"{ex}_") for ex in exclude):
            continue

        dest = dest_dir / item.name
        if item.suffix == ".yaml":
            # Track persona IDs from YAML files
            with open(item, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            persona_id = data.get("id", stem)
            # Don't count instruction file stems as persona IDs
            if persona_id not in exclude:
                persona_ids.append(persona_id)

        if not dest.exists():
            content = item.read_text(encoding="utf-8")
            content = content.replace("{{ORG_NAME}}", org_name)
            dest.write_text(content, encoding="utf-8")

        # Also copy to prompts/ subdirectory for instruction files
        if item.suffix == ".md":
            prompts_dest = dest_dir / "prompts" / item.name
            if not prompts_dest.exists():
                content = item.read_text(encoding="utf-8")
                content = content.replace("{{ORG_NAME}}", org_name)
                prompts_dest.parent.mkdir(parents=True, exist_ok=True)
                prompts_dest.write_text(content, encoding="utf-8")

    return persona_ids


def _generate_huddle_config(personas_dest: Path, advisor_ids: list[str]) -> None:
    """Generate the huddle YAML with read-only mounts for all advisors."""
    # Build read_only_mounts list
    mounts = [
        {"path": f"/vaults/{aid}", "root_file": "second-brain.md"}
        for aid in advisor_ids
    ]

    huddle_config = {
        "id": "huddle",
        "name": "The Huddle",
        "title": "Advisory Group Session",
        "tagline": "Where your team debates, disagrees, and converges",
        "model": {"max_tokens": 8192, "temperature": 0.8},
        "voice": {"engine": "disabled", "voice_id": "", "speed": 1.0},
        "vault": {
            "path": "/vaults/huddle",
            "root_file": "second-brain.md",
            "read_only_mounts": mounts,
            "writable_paths": ["/vaults/huddle"],
        },
        "memory": {"max_context_tokens": 6000},
        "delegation": {"can_delegate_to": [], "accepts_from": ["axon"]},
        "behavior": {"auto_save": True, "first_message": True, "proactive_checks": []},
        "ui": {"color": "#F59E0B", "avatar": "", "sparkle_color": "#FBBF24"},
        "system_prompt_file": "huddle_instructions.md",
    }

    huddle_path = personas_dest / "huddle.yaml"
    with open(huddle_path, "w", encoding="utf-8") as f:
        yaml.dump(huddle_config, f, default_flow_style=False, sort_keys=False)


def _generate_huddle_instructions(
    personas_dest: Path,
    template_personas_dir: Path,
    advisor_ids: list[str],
) -> None:
    """Generate huddle instructions with the advisor roster filled in."""
    # Build roster section from advisor YAML files
    roster_lines = []
    for aid in advisor_ids:
        yaml_path = template_personas_dir / f"{aid}.yaml"
        if yaml_path.exists():
            with open(yaml_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            name = data.get("name", aid.title())
            title = data.get("title", "")
            tagline = data.get("tagline", "")
            roster_lines.append(f"### {name} — {title} (\"{tagline}\")")
        else:
            roster_lines.append(f"### {aid.title()}")

    roster = "\n\n".join(roster_lines)

    # Load base huddle instructions template
    base_instructions = BASE_DIR / "personas" / "huddle_instructions.md"
    if base_instructions.exists():
        content = base_instructions.read_text(encoding="utf-8")
        content = content.replace("{{ADVISOR_ROSTER}}", roster)
    else:
        content = f"# The Huddle\n\n## The Advisors\n\n{roster}\n"

    # Write to both locations
    for dest in [
        personas_dest / "huddle_instructions.md",
        personas_dest / "prompts" / "huddle_instructions.md",
    ]:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")

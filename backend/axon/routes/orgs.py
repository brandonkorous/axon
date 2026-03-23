"""Organization management routes."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from axon.config import settings
import axon.registry as registry
from axon.org import OrgConfig, scaffold_org, load_org_config
from axon.org_templates import list_templates, get_template, scaffold_from_template

router = APIRouter()


class CreateOrgRequest(BaseModel):
    """Request body for creating a new organization."""

    id: str
    name: str
    description: str = ""
    template: str = ""  # org template ID (family, startup, etc.)


@router.get("")
async def list_orgs():
    """List all organizations."""
    return {"orgs": registry.list_orgs()}


@router.get("/templates")
async def get_templates():
    """List all available org type templates."""
    return {"templates": list_templates()}


@router.get("/templates/{template_id}")
async def get_template_detail(template_id: str):
    """Get details for a specific org template."""
    template = get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
    return template


@router.get("/{org_id}")
async def get_org(org_id: str):
    """Get details for a specific organization."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization not found: {org_id}")

    return {
        "id": org.config.id,
        "name": org.config.name,
        "description": org.config.description,
        "type": org.config.type,
        "agents": [
            {
                "id": agent.id,
                "name": agent.name,
                "title": agent.config.title,
            }
            for agent in org.agent_registry.values()
        ],
        "has_huddle": org.huddle is not None,
        "has_shared_vault": org.shared_vault is not None,
    }


@router.post("")
async def create_org(body: CreateOrgRequest):
    """Create a new organization.

    If `template` is provided, scaffolds from that template with curated personas.
    Otherwise, creates an empty org with just a shared vault.
    """
    orgs_dir = settings.axon_orgs_dir
    if not orgs_dir:
        raise HTTPException(
            status_code=400,
            detail="Multi-org mode not enabled. Set AXON_ORGS_DIR to enable.",
        )

    org_path = Path(orgs_dir) / body.id
    if org_path.exists():
        raise HTTPException(status_code=409, detail=f"Organization already exists: {body.id}")

    if body.template:
        # Scaffold from template (includes personas, vaults, etc.)
        try:
            scaffold_from_template(
                Path(orgs_dir), body.id, body.template, body.name
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        scaffold_org(org_path, org_name=body.name, org_description=body.description)

    # Initialize the org's agents and register it live
    from axon.main import _init_org_agents

    org_config = load_org_config(org_path)
    org = _init_org_agents(org_path, org_config)
    registry.org_registry[body.id] = org

    return {
        "status": "created",
        "id": body.id,
        "name": body.name,
        "template": body.template or None,
        "agent_count": len(org.agent_registry),
        "path": str(org_path),
    }

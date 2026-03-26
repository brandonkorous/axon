"""Organization management routes."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from axon.config import settings
import axon.registry as registry
from axon.org import OrgCommsConfig, OrgConfig, OrgType, scaffold_org, load_org_config
from axon.org_templates import list_templates, get_template, scaffold_from_template

logger = logging.getLogger(__name__)

router = APIRouter()


class CreateOrgRequest(BaseModel):
    """Request body for creating a new organization."""

    id: str
    name: str
    description: str = ""
    template: str = ""  # org template ID (family, startup, etc.)


class UpdateCommsRequest(BaseModel):
    """Updatable comms fields."""

    require_approval: bool | None = None
    email_domain: str | None = None
    email_signature: str | None = None
    inbound_polling: bool | None = None


class UpdateOrgRequest(BaseModel):
    """Request body for updating an organization."""

    name: str | None = None
    description: str | None = None
    type: OrgType | None = None
    comms: UpdateCommsRequest | None = None


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
        "comms": {
            "require_approval": org.config.comms.require_approval,
            "email_domain": org.config.comms.email_domain,
            "email_signature": org.config.comms.email_signature,
            "inbound_polling": org.config.comms.inbound_polling,
        },
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


@router.patch("/{org_id}")
async def update_org(org_id: str, body: UpdateOrgRequest):
    """Update an organization's name, description, or type."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization not found: {org_id}")

    orgs_dir = settings.axon_orgs_dir
    if not orgs_dir:
        raise HTTPException(status_code=400, detail="Multi-org mode not enabled.")

    # Persist to org.yaml
    yaml_path = Path(orgs_dir) / org_id / "org.yaml"
    if not yaml_path.exists():
        raise HTTPException(status_code=500, detail="org.yaml not found")

    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if body.name is not None:
        data["name"] = body.name
        org.config.name = body.name
    if body.description is not None:
        data["description"] = body.description
        org.config.description = body.description
    if body.type is not None:
        data["type"] = body.type.value
        org.config.type = body.type
    if body.comms is not None:
        comms_data = data.setdefault("comms", {})
        if body.comms.require_approval is not None:
            comms_data["require_approval"] = body.comms.require_approval
            org.config.comms.require_approval = body.comms.require_approval
        if body.comms.email_domain is not None:
            comms_data["email_domain"] = body.comms.email_domain
            org.config.comms.email_domain = body.comms.email_domain
        if body.comms.email_signature is not None:
            comms_data["email_signature"] = body.comms.email_signature
            org.config.comms.email_signature = body.comms.email_signature
        if body.comms.inbound_polling is not None:
            comms_data["inbound_polling"] = body.comms.inbound_polling
            org.config.comms.inbound_polling = body.comms.inbound_polling

    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    logger.info("Organization '%s' updated", org_id)

    return {
        "id": org.config.id,
        "name": org.config.name,
        "description": org.config.description,
        "type": org.config.type,
        "comms": {
            "require_approval": org.config.comms.require_approval,
            "email_domain": org.config.comms.email_domain,
            "email_signature": org.config.comms.email_signature,
            "inbound_polling": org.config.comms.inbound_polling,
        },
    }


@router.post("")
async def create_org(body: CreateOrgRequest):
    """Create a new organization.

    If `template` is provided, scaffolds from that template with curated agents.
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
        # Scaffold from template (includes agent vaults, shared vault, etc.)
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

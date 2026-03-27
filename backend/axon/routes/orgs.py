"""Organization management routes."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from axon.config import settings
from axon.db.engine import get_session
from axon.db.crud import org_settings as org_settings_crud
import axon.registry as registry
from axon.org import DiscordConfig, SlackConfig, TeamsConfig, ZoomConfig, OrgCommsConfig, OrgConfig, OrgType, scaffold_org, load_org_config
from axon.org_templates import list_templates, get_template, scaffold_from_template

logger = logging.getLogger(__name__)

router = APIRouter()


class CreateOrgRequest(BaseModel):
    """Request body for creating a new organization."""

    id: str
    name: str
    description: str = ""
    template: str = ""  # org template ID (family, startup, etc.)


class UpdateDiscordRequest(BaseModel):
    """Updatable Discord fields."""

    guild_id: str | None = None
    channel_mappings: dict[str, str] | None = None


class UpdateSlackRequest(BaseModel):
    """Updatable Slack fields."""

    channel_mappings: dict[str, str] | None = None


class UpdateTeamsRequest(BaseModel):
    """Updatable Teams fields."""

    tenant_id: str | None = None
    channel_mappings: dict[str, str] | None = None


class UpdateZoomRequest(BaseModel):
    """Updatable Zoom fields."""

    channel_mappings: dict[str, str] | None = None


class UpdateCommsRequest(BaseModel):
    """Updatable comms fields."""

    require_approval: bool | None = None
    email_domain: str | None = None
    email_signature: str | None = None
    inbound_polling: bool | None = None
    discord: UpdateDiscordRequest | None = None
    slack: UpdateSlackRequest | None = None
    teams: UpdateTeamsRequest | None = None
    zoom: UpdateZoomRequest | None = None


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
            "discord": {
                "guild_id": (org.config.comms.discord or DiscordConfig()).guild_id,
                "channel_mappings": (org.config.comms.discord or DiscordConfig()).channel_mappings,
            },
            "slack": {
                "channel_mappings": (org.config.comms.slack or SlackConfig()).channel_mappings,
            },
            "teams": {
                "tenant_id": (org.config.comms.teams or TeamsConfig()).tenant_id,
                "channel_mappings": (org.config.comms.teams or TeamsConfig()).channel_mappings,
            },
            "zoom": {
                "channel_mappings": (org.config.comms.zoom or ZoomConfig()).channel_mappings,
            },
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
async def update_org(
    org_id: str,
    body: UpdateOrgRequest,
    session: AsyncSession = Depends(get_session),
):
    """Update an organization's name, description, or type.

    Persists to both the central DB (primary) and org.yaml (backup).
    """
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization not found: {org_id}")

    # Build patch dict for DB update
    patch: dict = {}
    if body.name is not None:
        patch["name"] = body.name
        org.config.name = body.name
    if body.description is not None:
        patch["description"] = body.description
        org.config.description = body.description
    if body.type is not None:
        patch["type"] = body.type.value
        org.config.type = body.type
    if body.comms is not None:
        comms_patch: dict = {}
        if body.comms.require_approval is not None:
            comms_patch["require_approval"] = body.comms.require_approval
            org.config.comms.require_approval = body.comms.require_approval
        if body.comms.email_domain is not None:
            comms_patch["email_domain"] = body.comms.email_domain
            org.config.comms.email_domain = body.comms.email_domain
        if body.comms.email_signature is not None:
            comms_patch["email_signature"] = body.comms.email_signature
            org.config.comms.email_signature = body.comms.email_signature
        if body.comms.inbound_polling is not None:
            comms_patch["inbound_polling"] = body.comms.inbound_polling
            org.config.comms.inbound_polling = body.comms.inbound_polling
        if body.comms.discord is not None:
            discord_cfg = org.config.comms.discord or DiscordConfig()
            discord_patch: dict = {}
            if body.comms.discord.guild_id is not None:
                discord_patch["guild_id"] = body.comms.discord.guild_id
                discord_cfg.guild_id = body.comms.discord.guild_id
            if body.comms.discord.channel_mappings is not None:
                discord_patch["channel_mappings"] = body.comms.discord.channel_mappings
                discord_cfg.channel_mappings = body.comms.discord.channel_mappings
            if discord_patch:
                comms_patch["discord"] = discord_patch
                org.config.comms.discord = discord_cfg
        if body.comms.slack is not None:
            slack_cfg = org.config.comms.slack or SlackConfig()
            slack_patch: dict = {}
            if body.comms.slack.channel_mappings is not None:
                slack_patch["channel_mappings"] = body.comms.slack.channel_mappings
                slack_cfg.channel_mappings = body.comms.slack.channel_mappings
            if slack_patch:
                comms_patch["slack"] = slack_patch
                org.config.comms.slack = slack_cfg
        if body.comms.teams is not None:
            teams_cfg = org.config.comms.teams or TeamsConfig()
            teams_patch: dict = {}
            if body.comms.teams.tenant_id is not None:
                teams_patch["tenant_id"] = body.comms.teams.tenant_id
                teams_cfg.tenant_id = body.comms.teams.tenant_id
            if body.comms.teams.channel_mappings is not None:
                teams_patch["channel_mappings"] = body.comms.teams.channel_mappings
                teams_cfg.channel_mappings = body.comms.teams.channel_mappings
            if teams_patch:
                comms_patch["teams"] = teams_patch
                org.config.comms.teams = teams_cfg
        if body.comms.zoom is not None:
            zoom_cfg = org.config.comms.zoom or ZoomConfig()
            zoom_patch: dict = {}
            if body.comms.zoom.channel_mappings is not None:
                zoom_patch["channel_mappings"] = body.comms.zoom.channel_mappings
                zoom_cfg.channel_mappings = body.comms.zoom.channel_mappings
            if zoom_patch:
                comms_patch["zoom"] = zoom_patch
                org.config.comms.zoom = zoom_cfg
        if comms_patch:
            patch["comms"] = comms_patch

    # Primary: persist to central DB
    await org_settings_crud.update_settings(session, org_id, patch)

    # Backup: also persist to org.yaml
    orgs_dir = settings.axon_orgs_dir
    if orgs_dir:
        yaml_path = Path(orgs_dir) / org_id / "org.yaml"
        if yaml_path.exists():
            try:
                with open(yaml_path, encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                if body.name is not None:
                    data["name"] = body.name
                if body.description is not None:
                    data["description"] = body.description
                if body.type is not None:
                    data["type"] = body.type.value
                if body.comms is not None:
                    comms_data = data.setdefault("comms", {})
                    comms_data.update(patch.get("comms", {}))
                with open(yaml_path, "w", encoding="utf-8") as f:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            except Exception:
                logger.warning("Failed to write org.yaml backup for %s", org_id)

    logger.info("Organization '%s' updated", org_id)

    # Reload bot channel maps if integration config changed
    if body.comms is not None:
        from axon.bot_manager import on_config_changed
        await on_config_changed(body.comms)

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
            "discord": {
                "guild_id": (org.config.comms.discord or DiscordConfig()).guild_id,
                "channel_mappings": (org.config.comms.discord or DiscordConfig()).channel_mappings,
            },
            "slack": {
                "channel_mappings": (org.config.comms.slack or SlackConfig()).channel_mappings,
            },
            "teams": {
                "tenant_id": (org.config.comms.teams or TeamsConfig()).tenant_id,
                "channel_mappings": (org.config.comms.teams or TeamsConfig()).channel_mappings,
            },
            "zoom": {
                "channel_mappings": (org.config.comms.zoom or ZoomConfig()).channel_mappings,
            },
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

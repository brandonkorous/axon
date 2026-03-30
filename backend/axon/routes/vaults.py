"""Vault routes — CRUD operations and graph API for the memory browser."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from axon.config import settings
import axon.registry as registry
from axon.vault.frontmatter import parse_frontmatter, write_frontmatter

router = APIRouter()
org_router = APIRouter()


class FileWriteRequest(BaseModel):
    """Request body for creating/updating a vault file."""

    content: str
    frontmatter: dict[str, Any] = {}


class LinkRequest(BaseModel):
    """Request body for creating a wikilink between files."""

    from_path: str
    to_path: str
    section: str | None = None


def _get_agent_or_404(agent_reg: dict, agent_id: str, org_id: str = ""):
    """Resolve an agent from a registry or raise 404."""
    agent = agent_reg.get(agent_id)
    if not agent:
        detail = f"Agent not found: {agent_id}"
        if org_id:
            detail += f" in org {org_id}"
        raise HTTPException(status_code=404, detail=detail)
    return agent


# ── Shared implementation ───────────────────────────────────────────


async def _get_vault_graph(agent):
    return agent.vault.graph.to_json()


async def _get_vault_graph_neighborhood(agent, file_path: str, depth: int = 2):
    return agent.vault.graph.get_neighborhood(file_path, depth)


async def _get_vault_graph_stats(agent):
    return agent.vault.graph.get_stats()


def _list_vault_files_sync(agent, branch: str | None = None):
    """List vault files (sync — runs in thread)."""
    if branch:
        return agent.vault.list_branch(branch)
    vault_path = Path(agent.config.vault.path)
    files = []
    for item in sorted(vault_path.iterdir()):
        if item.is_dir() and not item.name.startswith("."):
            files.append({
                "name": item.name,
                "type": "directory",
                "file_count": len(list(item.glob("*.md"))),
            })
        elif item.suffix == ".md":
            files.append({
                "name": item.name,
                "type": "file",
                "path": item.name,
            })
    return files


async def _list_vault_files(agent, branch: str | None = None):
    import asyncio
    files = await asyncio.to_thread(_list_vault_files_sync, agent, branch)
    return {"agent_id": agent.id, "branch": branch, "files": files}


async def _read_vault_file(agent, file_path: str):
    try:
        metadata, body = agent.vault.read_file(file_path)
        links = agent.vault.get_links(file_path)
        backlinks = agent.vault.get_backlinks(file_path)
        return {
            "path": file_path,
            "frontmatter": metadata,
            "content": body,
            "links": links,
            "backlinks": backlinks,
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")


async def _write_vault_file(agent, file_path: str, body: FileWriteRequest):
    try:
        agent.vault.write_file(file_path, body.frontmatter, body.content)
        return {"status": "ok", "path": file_path}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


async def _delete_vault_file(agent, file_path: str):
    full_path = Path(agent.config.vault.path) / file_path
    if not full_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    full_path.unlink()
    agent.vault.cache.remove(file_path)
    agent.vault._invalidate_graph()
    return {"status": "deleted", "path": file_path}


async def _search_vault(agent, q: str):
    results = agent.vault.search(q)
    return {"query": q, "results": results}


async def _create_link(agent, body: LinkRequest):
    try:
        agent.vault.add_link(body.from_path, body.to_path, body.section)
        return {"status": "ok", "from": body.from_path, "to": body.to_path}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Legacy routes (default org) ─────────────────────────────────────


@router.get("/{agent_id}/graph")
async def get_vault_graph(agent_id: str):
    agent = _get_agent_or_404(registry.agent_registry, agent_id)
    return await _get_vault_graph(agent)


@router.get("/{agent_id}/graph/stats")
async def get_vault_graph_stats(agent_id: str):
    agent = _get_agent_or_404(registry.agent_registry, agent_id)
    return await _get_vault_graph_stats(agent)


@router.get("/{agent_id}/graph/neighborhood/{file_path:path}")
async def get_vault_graph_neighborhood(agent_id: str, file_path: str, depth: int = 2):
    agent = _get_agent_or_404(registry.agent_registry, agent_id)
    return await _get_vault_graph_neighborhood(agent, file_path, depth)


@router.get("/{agent_id}/files")
async def list_vault_files(agent_id: str, branch: str | None = None):
    agent = _get_agent_or_404(registry.agent_registry, agent_id)
    return await _list_vault_files(agent, branch)


@router.get("/{agent_id}/files/{file_path:path}")
async def read_vault_file(agent_id: str, file_path: str):
    agent = _get_agent_or_404(registry.agent_registry, agent_id)
    return await _read_vault_file(agent, file_path)


@router.put("/{agent_id}/files/{file_path:path}")
async def write_vault_file(agent_id: str, file_path: str, body: FileWriteRequest):
    agent = _get_agent_or_404(registry.agent_registry, agent_id)
    return await _write_vault_file(agent, file_path, body)


@router.delete("/{agent_id}/files/{file_path:path}")
async def delete_vault_file(agent_id: str, file_path: str):
    agent = _get_agent_or_404(registry.agent_registry, agent_id)
    return await _delete_vault_file(agent, file_path)


@router.get("/{agent_id}/search")
async def search_vault(agent_id: str, q: str):
    agent = _get_agent_or_404(registry.agent_registry, agent_id)
    return await _search_vault(agent, q)


@router.post("/{agent_id}/link")
async def create_link(agent_id: str, body: LinkRequest):
    agent = _get_agent_or_404(registry.agent_registry, agent_id)
    return await _create_link(agent, body)


# ── Org-scoped routes ───────────────────────────────────────────────


@org_router.get("/resolve/{file_path:path}")
async def resolve_org_vault_file(org_id: str, file_path: str):
    """Search all vaults in the org for a file and return the first match."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization not found: {org_id}")
    for aid, agent in org.agent_registry.items():
        try:
            result = await _read_vault_file(agent, file_path)
            return {**result, "vault_id": aid}
        except HTTPException:
            continue
    raise HTTPException(status_code=404, detail=f"File not found in any vault: {file_path}")


@org_router.get("/{agent_id}/graph")
async def get_org_vault_graph(org_id: str, agent_id: str):
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization not found: {org_id}")
    agent = _get_agent_or_404(org.agent_registry, agent_id, org_id)
    return await _get_vault_graph(agent)


@org_router.get("/{agent_id}/graph/stats")
async def get_org_vault_graph_stats(org_id: str, agent_id: str):
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization not found: {org_id}")
    agent = _get_agent_or_404(org.agent_registry, agent_id, org_id)
    return await _get_vault_graph_stats(agent)


@org_router.get("/{agent_id}/graph/neighborhood/{file_path:path}")
async def get_org_vault_graph_neighborhood(org_id: str, agent_id: str, file_path: str, depth: int = 2):
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization not found: {org_id}")
    agent = _get_agent_or_404(org.agent_registry, agent_id, org_id)
    return await _get_vault_graph_neighborhood(agent, file_path, depth)


@org_router.get("/{agent_id}/files")
async def list_org_vault_files(org_id: str, agent_id: str, branch: str | None = None):
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization not found: {org_id}")
    agent = _get_agent_or_404(org.agent_registry, agent_id, org_id)
    return await _list_vault_files(agent, branch)


@org_router.get("/{agent_id}/files/{file_path:path}")
async def read_org_vault_file(org_id: str, agent_id: str, file_path: str):
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization not found: {org_id}")
    agent = _get_agent_or_404(org.agent_registry, agent_id, org_id)
    return await _read_vault_file(agent, file_path)


@org_router.put("/{agent_id}/files/{file_path:path}")
async def write_org_vault_file(org_id: str, agent_id: str, file_path: str, body: FileWriteRequest):
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization not found: {org_id}")
    agent = _get_agent_or_404(org.agent_registry, agent_id, org_id)
    return await _write_vault_file(agent, file_path, body)


@org_router.delete("/{agent_id}/files/{file_path:path}")
async def delete_org_vault_file(org_id: str, agent_id: str, file_path: str):
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization not found: {org_id}")
    agent = _get_agent_or_404(org.agent_registry, agent_id, org_id)
    return await _delete_vault_file(agent, file_path)


@org_router.get("/{agent_id}/search")
async def search_org_vault(org_id: str, agent_id: str, q: str):
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization not found: {org_id}")
    agent = _get_agent_or_404(org.agent_registry, agent_id, org_id)
    return await _search_vault(agent, q)


@org_router.post("/{agent_id}/link")
async def create_org_link(org_id: str, agent_id: str, body: LinkRequest):
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization not found: {org_id}")
    agent = _get_agent_or_404(org.agent_registry, agent_id, org_id)
    return await _create_link(agent, body)


# ── Deep Memory Review ────────────────────────────────────────────


class DeepReviewAction(BaseModel):
    """Request body for acting on a deep memory."""

    action: str  # "reinvigorate" or "delete"


@org_router.get("/{agent_id}/memory/deep-review")
async def list_deep_memories(org_id: str, agent_id: str):
    """List deep memories available for user review."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization not found: {org_id}")
    agent = _get_agent_or_404(org.agent_registry, agent_id, org_id)
    if not agent.memory_manager:
        raise HTTPException(status_code=400, detail="Memory not enabled for this agent")
    return {"memories": agent.memory_manager.list_deep_for_review()}


@org_router.post("/{agent_id}/memory/deep-review/{file_path:path}")
async def act_on_deep_memory(org_id: str, agent_id: str, file_path: str, body: DeepReviewAction):
    """Reinvigorate or permanently delete a deep memory."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization not found: {org_id}")
    agent = _get_agent_or_404(org.agent_registry, agent_id, org_id)
    if not agent.memory_manager:
        raise HTTPException(status_code=400, detail="Memory not enabled for this agent")

    if body.action == "reinvigorate":
        new_path = agent.memory_manager.reinvigorate(file_path)
        if new_path:
            return {"status": "reinvigorated", "new_path": new_path}
        raise HTTPException(status_code=500, detail="Failed to reinvigorate memory")
    elif body.action == "delete":
        if agent.memory_manager.delete_deep_memory(file_path):
            return {"status": "deleted"}
        raise HTTPException(status_code=500, detail="Failed to delete memory")
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {body.action}")

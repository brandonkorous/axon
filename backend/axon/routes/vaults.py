"""Vault routes — CRUD operations and graph API for the memory browser."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from axon.config import settings
from axon.main import agent_registry
from axon.vault.frontmatter import parse_frontmatter, write_frontmatter
from axon.vault.graph import VaultGraph

router = APIRouter()


class FileWriteRequest(BaseModel):
    """Request body for creating/updating a vault file."""

    content: str
    frontmatter: dict[str, Any] = {}


class LinkRequest(BaseModel):
    """Request body for creating a wikilink between files."""

    from_path: str
    to_path: str
    section: str | None = None


# ── Graph API ────────────────────────────────────────────────────────


@router.get("/{agent_id}/graph")
async def get_vault_graph(agent_id: str):
    """Get the full wikilink graph for an agent's vault (for the memory browser)."""
    agent = agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    graph = VaultGraph.build(agent.config.vault.path)
    return graph.to_json()


# ── File CRUD ────────────────────────────────────────────────────────


@router.get("/{agent_id}/files")
async def list_vault_files(agent_id: str, branch: str | None = None):
    """List files in an agent's vault, optionally filtered by branch."""
    agent = agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    if branch:
        files = agent.vault.list_branch(branch)
    else:
        # List all branches
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

    return {"agent_id": agent_id, "branch": branch, "files": files}


@router.get("/{agent_id}/files/{file_path:path}")
async def read_vault_file(agent_id: str, file_path: str):
    """Read a specific file from an agent's vault."""
    agent = agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

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


@router.put("/{agent_id}/files/{file_path:path}")
async def write_vault_file(agent_id: str, file_path: str, body: FileWriteRequest):
    """Create or update a file in an agent's vault."""
    agent = agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    try:
        agent.vault.write_file(file_path, body.frontmatter, body.content)
        return {"status": "ok", "path": file_path}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{agent_id}/files/{file_path:path}")
async def delete_vault_file(agent_id: str, file_path: str):
    """Delete a file from an agent's vault."""
    agent = agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    full_path = Path(agent.config.vault.path) / file_path
    if not full_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    full_path.unlink()
    agent.vault._invalidate_graph()
    return {"status": "deleted", "path": file_path}


# ── Search ───────────────────────────────────────────────────────────


@router.get("/{agent_id}/search")
async def search_vault(agent_id: str, q: str):
    """Full-text search across an agent's vault."""
    agent = agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    results = agent.vault.search(q)
    return {"query": q, "results": results}


# ── Links ────────────────────────────────────────────────────────────


@router.post("/{agent_id}/link")
async def create_link(agent_id: str, body: LinkRequest):
    """Create a wikilink between two files in an agent's vault."""
    agent = agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    try:
        agent.vault.add_link(body.from_path, body.to_path, body.section)
        return {"status": "ok", "from": body.from_path, "to": body.to_path}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

"""Git repository management routes."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from axon.db.engine import get_session
from axon.db.crud import git_repos as crud
from axon.logging import get_logger
import axon.registry as registry

logger = get_logger(__name__)

org_router = APIRouter()

VALID_CLONE_STRATEGIES = {"shallow", "full", "sparse"}


class CreateRepoRequest(BaseModel):
    url: str
    name: str
    default_branch: str = "main"
    auth_credential_id: str | None = None
    clone_strategy: str = "shallow"
    sparse_paths: list[str] = []


class UpdateRepoRequest(BaseModel):
    url: str | None = None
    name: str | None = None
    default_branch: str | None = None
    auth_credential_id: str | None = None
    clone_strategy: str | None = None
    sparse_paths: list[str] | None = None


def _validate_strategy(strategy: str, sparse_paths: list[str] | None) -> None:
    """Validate clone strategy and sparse paths combination."""
    if strategy not in VALID_CLONE_STRATEGIES:
        raise HTTPException(
            400,
            f"Invalid clone_strategy. Must be one of: {', '.join(sorted(VALID_CLONE_STRATEGIES))}",
        )
    if sparse_paths and strategy != "sparse":
        raise HTTPException(400, "sparse_paths can only be set when clone_strategy is 'sparse'")


def _repo_to_dict(repo) -> dict:
    """Serialise a GitRepository row to a JSON-safe dict."""
    return {
        "id": repo.id,
        "org_id": repo.org_id,
        "url": repo.url,
        "name": repo.name,
        "default_branch": repo.default_branch,
        "auth_credential_id": repo.auth_credential_id,
        "clone_strategy": repo.clone_strategy,
        "sparse_paths": json.loads(repo.sparse_paths_json),
        "created_at": repo.created_at.isoformat() if repo.created_at else None,
        "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
    }


@org_router.get("")
async def list_repos(org_id: str, session: AsyncSession = Depends(get_session)):
    """List git repositories for an org."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Organization not found: {org_id}")
    repos = await crud.get_org_repos(session, org_id)
    return [_repo_to_dict(r) for r in repos]


@org_router.post("")
async def create_repo(
    org_id: str,
    body: CreateRepoRequest,
    session: AsyncSession = Depends(get_session),
):
    """Create a git repository configuration."""
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Organization not found: {org_id}")

    _validate_strategy(body.clone_strategy, body.sparse_paths)

    repo = await crud.create_repo(
        session,
        org_id=org_id,
        url=body.url,
        name=body.name,
        default_branch=body.default_branch,
        auth_credential_id=body.auth_credential_id,
        clone_strategy=body.clone_strategy,
        sparse_paths=body.sparse_paths,
    )
    logger.info("Created git repo '%s' for org %s", body.name, org_id)
    return _repo_to_dict(repo)


@org_router.get("/{repo_id}")
async def get_repo(
    org_id: str,
    repo_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get a git repository by ID."""
    repo = await crud.get_repo(session, repo_id)
    if not repo or repo.org_id != org_id:
        raise HTTPException(404, "Repository not found")
    return _repo_to_dict(repo)


@org_router.patch("/{repo_id}")
async def update_repo(
    org_id: str,
    repo_id: str,
    body: UpdateRepoRequest,
    session: AsyncSession = Depends(get_session),
):
    """Update a git repository configuration."""
    existing = await crud.get_repo(session, repo_id)
    if not existing or existing.org_id != org_id:
        raise HTTPException(404, "Repository not found")

    updates = body.model_dump(exclude_none=True)
    if not updates:
        return _repo_to_dict(existing)

    # Validate strategy (use new value or fall back to existing)
    strategy = updates.get("clone_strategy", existing.clone_strategy)
    sparse = updates.get("sparse_paths", json.loads(existing.sparse_paths_json))
    _validate_strategy(strategy, sparse)

    repo = await crud.update_repo(session, repo_id, **updates)
    logger.info("Updated git repo %s for org %s", repo_id, org_id)
    return _repo_to_dict(repo)


@org_router.delete("/{repo_id}")
async def delete_repo(
    org_id: str,
    repo_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Delete a git repository configuration."""
    existing = await crud.get_repo(session, repo_id)
    if not existing or existing.org_id != org_id:
        raise HTTPException(404, "Repository not found")

    await crud.delete_repo(session, repo_id)
    logger.info("Deleted git repo %s for org %s", repo_id, org_id)
    return {"status": "deleted"}

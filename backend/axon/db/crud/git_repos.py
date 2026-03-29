"""CRUD operations for git repository configurations."""

from __future__ import annotations

import json
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from axon.db.models import GitRepository


async def create_repo(
    session: AsyncSession,
    *,
    org_id: str,
    url: str,
    name: str,
    default_branch: str = "main",
    auth_credential_id: str | None = None,
    clone_strategy: str = "shallow",
    sparse_paths: list[str] | None = None,
) -> GitRepository:
    """Create a git repository configuration."""
    repo = GitRepository(
        id=str(uuid.uuid4()),
        org_id=org_id,
        url=url,
        name=name,
        default_branch=default_branch,
        auth_credential_id=auth_credential_id,
        clone_strategy=clone_strategy,
        sparse_paths_json=json.dumps(sparse_paths or []),
    )
    session.add(repo)
    await session.commit()
    await session.refresh(repo)
    return repo


async def get_repo(session: AsyncSession, repo_id: str) -> GitRepository | None:
    """Fetch a git repository by ID."""
    return await session.get(GitRepository, repo_id)


async def get_org_repos(session: AsyncSession, org_id: str) -> list[GitRepository]:
    """List all git repositories for an org."""
    stmt = select(GitRepository).where(GitRepository.org_id == org_id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_repo(
    session: AsyncSession,
    repo_id: str,
    **kwargs: object,
) -> GitRepository | None:
    """Update a git repository configuration.

    Accepts keyword arguments matching GitRepository column names.
    The special key ``sparse_paths`` (a list) is serialised to
    ``sparse_paths_json`` automatically.
    """
    repo = await session.get(GitRepository, repo_id)
    if not repo:
        return None

    # Convert sparse_paths list to JSON column
    if "sparse_paths" in kwargs:
        kwargs["sparse_paths_json"] = json.dumps(kwargs.pop("sparse_paths") or [])

    for key, value in kwargs.items():
        if value is not None and hasattr(repo, key):
            setattr(repo, key, value)

    await session.commit()
    await session.refresh(repo)
    return repo


async def delete_repo(session: AsyncSession, repo_id: str) -> bool:
    """Delete a git repository configuration."""
    repo = await session.get(GitRepository, repo_id)
    if not repo:
        return False
    await session.delete(repo)
    await session.commit()
    return True

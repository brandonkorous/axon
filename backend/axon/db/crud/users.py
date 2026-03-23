"""CRUD operations for users."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from axon.db.models import User


async def create_user(
    session: AsyncSession,
    *,
    email: str,
    display_name: str,
    org_id: str,
    role: str = "member",
) -> User:
    """Create a new user."""
    user = User(
        id=str(uuid.uuid4()),
        email=email,
        display_name=display_name,
        org_id=org_id,
        role=role,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user(session: AsyncSession, user_id: str) -> User | None:
    """Fetch a user by ID."""
    return await session.get(User, user_id)


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Fetch a user by email address."""
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_org_users(session: AsyncSession, org_id: str) -> list[User]:
    """List all users in an organization."""
    stmt = select(User).where(User.org_id == org_id).order_by(User.display_name)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_user(
    session: AsyncSession,
    user_id: str,
    *,
    display_name: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
) -> User | None:
    """Update user fields."""
    user = await session.get(User, user_id)
    if not user:
        return None
    if display_name is not None:
        user.display_name = display_name
    if role is not None:
        user.role = role
    if is_active is not None:
        user.is_active = is_active
    await session.commit()
    await session.refresh(user)
    return user


async def delete_user(session: AsyncSession, user_id: str) -> bool:
    """Delete a user and their connected accounts (cascade)."""
    user = await session.get(User, user_id)
    if not user:
        return False
    await session.delete(user)
    await session.commit()
    return True

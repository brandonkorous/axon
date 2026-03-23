"""Database models — provider-agnostic, works with SQLite and Postgres."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from axon.db.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """A user of the Axon platform."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(100))
    org_id: Mapped[str] = mapped_column(String(100), index=True)
    role: Mapped[str] = mapped_column(String(20), default="member")
    is_active: Mapped[bool] = mapped_column(default=True)

    connected_accounts: Mapped[list[ConnectedAccount]] = relationship(
        back_populates="user", cascade="all, delete-orphan",
    )


class Credential(Base, TimestampMixin):
    """An OAuth or API credential — tokens are AES-encrypted at rest."""

    __tablename__ = "credentials"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(100), index=True)
    provider: Mapped[str] = mapped_column(String(50), index=True)
    label: Mapped[str] = mapped_column(String(100), default="")
    access_token_enc: Mapped[str] = mapped_column(Text)
    refresh_token_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expiry: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    scopes: Mapped[str] = mapped_column(Text, default="")
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")

    connected_accounts: Mapped[list[ConnectedAccount]] = relationship(
        back_populates="credential", cascade="all, delete-orphan",
    )


class ConnectedAccount(Base, TimestampMixin):
    """Links a user to a credential for a specific provider account."""

    __tablename__ = "connected_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True,
    )
    credential_id: Mapped[str] = mapped_column(
        ForeignKey("credentials.id", ondelete="CASCADE"), index=True,
    )
    provider: Mapped[str] = mapped_column(String(50))
    provider_account_id: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)

    user: Mapped[User] = relationship(back_populates="connected_accounts")
    credential: Mapped[Credential] = relationship(back_populates="connected_accounts")

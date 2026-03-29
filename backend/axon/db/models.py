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


class OrgSettings(Base, TimestampMixin):
    """Organization settings — mirrors org.yaml but persisted in central DB."""

    __tablename__ = "org_settings"

    org_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    type: Mapped[str] = mapped_column(String(50), default="startup")
    comms_require_approval: Mapped[bool] = mapped_column(default=True)
    comms_email_domain: Mapped[str] = mapped_column(String(255), default="")
    comms_email_signature: Mapped[str] = mapped_column(Text, default="")
    comms_inbound_polling: Mapped[bool] = mapped_column(default=False)


class UserPreference(Base, TimestampMixin):
    """User preferences — theme, voice, display settings."""

    __tablename__ = "user_preferences"

    user_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    theme: Mapped[str] = mapped_column(String(20), default="dark")
    voice_settings_json: Mapped[str] = mapped_column(Text, default="{}")
    display_prefs_json: Mapped[str] = mapped_column(Text, default="{}")


class VapidKeys(Base, TimestampMixin):
    """VAPID key pair for Web Push — one row, generated on first boot."""

    __tablename__ = "vapid_keys"

    id: Mapped[str] = mapped_column(String(10), primary_key=True, default="default")
    public_key: Mapped[str] = mapped_column(Text)
    private_key_enc: Mapped[str] = mapped_column(Text)


class GitRepository(Base, TimestampMixin):
    """Git repository configuration for sandbox cloning."""

    __tablename__ = "git_repositories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(100), index=True)
    url: Mapped[str] = mapped_column(String(500))
    name: Mapped[str] = mapped_column(String(100))
    default_branch: Mapped[str] = mapped_column(String(100), default="main")
    auth_credential_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    clone_strategy: Mapped[str] = mapped_column(String(20), default="shallow")
    sparse_paths_json: Mapped[str] = mapped_column(Text, default="[]")


class PushSubscription(Base, TimestampMixin):
    """Browser push subscription endpoint."""

    __tablename__ = "push_subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    endpoint: Mapped[str] = mapped_column(Text, unique=True, index=True)
    p256dh: Mapped[str] = mapped_column(Text)
    auth: Mapped[str] = mapped_column(Text)
    user_id: Mapped[str] = mapped_column(String(36), default="default")

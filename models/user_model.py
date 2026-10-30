import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from models.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False),
        primary_key=True,
        default=uuid.uuid4,
    )

    first_name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    
    last_name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    
    contact: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    password_expires_at = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    country: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )

    state: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )

    zip_code: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )

    address: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )

    user_role_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user_roles.id"),
        nullable=False,
        index=True,
    )

    user_role = relationship(
        "UserRole",
        back_populates="users",
        lazy="select",
    )

    is_two_factor_authenticated: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    is_email_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    is_contact_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=utc_now,
        nullable=True,
    )

    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    deleted_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    deletion_reason: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )

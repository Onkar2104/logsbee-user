
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class VerificationOTP(Base):
    __tablename__ = "verification_otps"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # "email" or "whatsapp"
    channel: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    otp_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(),
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(),
        nullable=False,
    )

    attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(),
        nullable=True,
    )

    __table_args__ = (
        Index(
            "ix_verification_otp_lookup",
            "user_id",
            "channel",
            "created_at",
        ),
    )

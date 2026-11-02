import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Uuid, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


def utc_now():
    return datetime.now(timezone.utc)


class UserProduct(Base):
    __tablename__ = "user_products"
    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uq_user_products_user_product"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True, native_uuid=False), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True, native_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True, native_uuid=False), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    granted_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True, native_uuid=False), nullable=True)

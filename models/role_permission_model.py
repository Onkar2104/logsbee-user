import uuid

from sqlalchemy import ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False),
        ForeignKey("user_roles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    )

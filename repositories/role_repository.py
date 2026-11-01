import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from models.user_role_model import UserRole


class RoleRepository:
    @staticmethod
    def get_by_id(db: Session, role_id: uuid.UUID):
        return db.scalar(
            select(UserRole)
            .options(selectinload(UserRole.permissions))
            .where(UserRole.id == role_id, UserRole.is_deleted.is_(False))
        )

    @staticmethod
    def get_by_name(db: Session, account_id: uuid.UUID, name: str):
        return db.scalar(select(UserRole).where(
            UserRole.account_id == account_id,
            UserRole.name == name,
            UserRole.is_deleted.is_(False),
        ))

    @staticmethod
    def get_account_roles(db: Session, account_id: uuid.UUID):
        return list(db.scalars(
            select(UserRole).options(selectinload(UserRole.permissions)).where(
                UserRole.account_id == account_id,
                UserRole.is_deleted.is_(False),
                UserRole.is_system_role.is_(False),
            ).order_by(UserRole.name)
        ).all())

    @staticmethod
    def create(db: Session, role: UserRole):
        db.add(role)
        db.flush()
        return role

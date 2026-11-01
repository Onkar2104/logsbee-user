import uuid

from sqlalchemy import select, exists
from sqlalchemy.orm import Session

from models.user_model import User
from models.user_role_model import UserRole


class UserRepository:

    @staticmethod
    def get_by_id(db: Session, user_id: uuid.UUID):
        return db.scalar(select(User).where(User.id == user_id))

    @staticmethod
    def get_by_email(db: Session, email: str):
        return db.scalar(select(User).where(User.email == email))

    @staticmethod
    def email_exists(db: Session, email: str, exclude_user_id: uuid.UUID) -> bool:
        return bool(db.scalar(
            select(exists().where(User.email == email, User.id != exclude_user_id))
        ))

    @staticmethod
    def get_role_by_id(db: Session, role_id: uuid.UUID):
        return db.scalar(
            select(UserRole).where(
                UserRole.id == role_id,
                UserRole.is_deleted.is_(False),
            )
        )

    @staticmethod
    def role_exists(db: Session, role_id: uuid.UUID) -> bool:
        return UserRepository.get_role_by_id(db, role_id) is not None

    @staticmethod
    def get_by_user_role(db: Session, name: str):
        return db.scalar(
            select(UserRole).where(
                UserRole.name == name,
                UserRole.account_id.is_(None),
                UserRole.is_system_role.is_(True),
                UserRole.is_deleted.is_(False),
            )
        )

    @staticmethod
    def get_all_active(db: Session, account_id: uuid.UUID | None = None):
        query = select(User).where(User.is_deleted.is_(False))
        if account_id is not None:
            query = query.where(User.account_id == account_id)
        return list(db.scalars(query.order_by(User.created_at.desc())).all())

    @staticmethod
    def create(db: Session, user: User):
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update(db: Session, user: User):
        db.commit()
        db.refresh(user)
        return user

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.user_model import User
from models.user_role_model import UserRole


class UserRepository:

    @staticmethod
    def get_by_id(db: Session, user_id: uuid.UUID):
        return db.scalar(
            select(User).where(User.id == user_id)
        )

    @staticmethod
    def get_by_email(db: Session, email: str):
        return db.scalar(
            select(User).where(User.email == email)
        )

    @staticmethod
    def get_by_user_role(db: Session, name: str):
        return db.scalar(
            select(UserRole).where(UserRole.name == name)
        )

    @staticmethod
    def get_all_active(db: Session):
        return list(
            db.scalars(
                select(User)
                .where(User.is_deleted.is_(False))
                .order_by(User.created_at.desc())
            ).all()
        )

    @staticmethod
    def role_exists(db: Session, role_id: uuid.UUID) -> bool:
        return db.scalar(
            select(UserRole.id).where(UserRole.id == role_id)
        ) is not None

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

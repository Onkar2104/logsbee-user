import uuid

from sqlalchemy.orm import Session

from schemas.user_schema import UserCreate, UserUpdate
from services.user_service import UserService
from schemas.user_schema import PasswordChange


class UserController:

    @staticmethod
    def create_user(db: Session, data: UserCreate):
        return UserService.create_user(db, data)


    @staticmethod
    def get_users(db: Session):
        return UserService.get_users(db)


    @staticmethod
    def get_user(db: Session, user_id: uuid.UUID, current_user):
        return UserService.get_user(db, user_id, current_user)


    @staticmethod
    def update_user(
        db: Session,
        user_id: uuid.UUID,
        data: UserUpdate,
    ):
        return UserService.update_user(db, user_id, data)


    @staticmethod
    def delete_user(
        db: Session,
        user_id: uuid.UUID,
        deleted_by: uuid.UUID | None,
        reason: str | None,
    ):
        return UserService.delete_user(
            db, user_id, deleted_by, reason
        )


    @staticmethod
    def change_password(
        db: Session,
        user_id: uuid.UUID,
        data: PasswordChange,
    ):
        return UserService.change_password(db, user_id, data)
import uuid
from sqlalchemy.orm import Session

from schemas.user_schema import UserCreate, UserUpdate, PasswordChange
from services.user_service import UserService


class UserController:
    @staticmethod
    def create_user(db: Session, data: UserCreate, current_user):
        return UserService.create_user(db, data, current_user)

    @staticmethod
    def get_users(db: Session, current_user):
        return UserService.get_users(db, current_user)

    @staticmethod
    def get_user(db: Session, user_id: uuid.UUID, current_user):
        return UserService.get_user(db, user_id, current_user)

    @staticmethod
    def update_user(db: Session, user_id: uuid.UUID, data: UserUpdate, current_user):
        return UserService.update_user(db, user_id, data, current_user)

    @staticmethod
    def delete_user(db: Session, user_id: uuid.UUID, deleted_by, reason, current_user):
        return UserService.delete_user(db, user_id, deleted_by, reason, current_user)

    @staticmethod
    def change_password(db: Session, request: PasswordChange, current_user):
        return UserService.change_password(db, request, current_user)

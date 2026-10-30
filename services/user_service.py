
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from models.user_model import User
from core.security import hash_password, verify_password
from core.user_permissions import check_user_access, check_user_role
from schemas.user_schema import UserCreate, UserUpdate
from repositories.user_repository import UserRepository
from repositories.password_history_repository import PasswordHistoryRepository

from dateutil.relativedelta import relativedelta



class UserService:

    @staticmethod
    def create_user(db: Session, data: UserCreate):
        email = data.email.strip().lower()

        if UserRepository.get_by_email(db, email):
            raise HTTPException(
                status_code=409,
                detail="Email already exists",
            )

        default_role = UserRepository.get_by_user_role(
            db, "user"
        )

        if default_role is None:
            raise HTTPException(
                status_code=500,
                detail="Default user role is not configured",
            )

        user_data = data.model_dump(
            exclude={"email", "password"}
        )

        user_data["email"] = email
        user_data["password_hash"] = hash_password(
            data.password.get_secret_value()
        )
        user_data["user_role_id"] = default_role.id

        user = User(**user_data)

        return UserRepository.create(db, user)


    @staticmethod
    def get_users(db: Session, current_user):

        check_user_role(current_user)
        
        return UserRepository.get_all_active(db)


    @staticmethod
    def get_user(db: Session, user_id: uuid.UUID, current_user):

        check_user_access(current_user, user_id)

        user = UserRepository.get_by_id(db, user_id)

        if not user or user.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        return user


    @staticmethod
    def update_user(
        db: Session,
        user_id: uuid.UUID,
        data: UserUpdate,
        current_user,
    ):
        user = UserService.get_user(db, user_id, current_user)

        changes = data.model_dump(exclude_unset=True)

        if changes.get("email") is not None:
            email = changes["email"].strip().lower()

            if email != user.email:
                if UserRepository.email_exists(db, email, user.id):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Email already exists.",
                    )

            changes["email"] = email


        if "user_role_id" in changes:
            check_user_role(current_user)

            if changes["user_role_id"] is not None:
                if not UserRepository.role_exists(
                    db, changes["user_role_id"]
                ):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid or inactive user role.",
                    )

        
        for field, value in changes.items():
            setattr(user, field, value)

        user.updated_at = datetime.now(timezone.utc)

        try:
            return UserRepository.update(db, user)

        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists or invalid user role.",
            )


    @staticmethod
    def delete_user(
        db: Session,
        user_id: uuid.UUID,
        deleted_by: uuid.UUID | None,
        reason: str | None,
        current_user,
    ):
       
        user = UserService.get_user(db, user_id, current_user)

        user.is_deleted = True
        user.deleted_at = datetime.now(timezone.utc)
        user.deleted_by = current_user.id
        user.deletion_reason = reason

        return UserRepository.update(db, user)


    @staticmethod
    def change_password(db: Session, request, current_user):

        user = current_user

        if not user or user.is_deleted:
            raise HTTPException(
                status_code=404,
                detail="User not found",
            )

        current_password = request.current_password.get_secret_value()
        new_password = request.new_password.get_secret_value()

    
        if not verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=400,
                detail="Current password is incorrect",
            )

        
        if verify_password(new_password, user.password_hash):
            raise HTTPException(
                status_code=400,
                detail="New password must differ from current password",
            )

        history = PasswordHistoryRepository.get_last_five(
            db, user.id
        )

        for record in history:
            if verify_password(new_password, record.password_hash):
                raise HTTPException(
                    status_code=400,
                    detail="You cannot reuse any of your last 5 passwords",
                )

        now = datetime.now(timezone.utc)

        try:
            PasswordHistoryRepository.add(
                db, user.id, user.password_hash
            )

            PasswordHistoryRepository.keep_last_five(
                db, user.id
            )

            user.password_hash = hash_password(new_password)

            user.password_expires_at = now + relativedelta(months=1)

            user.updated_at = now

            db.commit()
            db.refresh(user)

            return {
                "message": "Password changed successfully"
            }

        except Exception:
            db.rollback()
            raise
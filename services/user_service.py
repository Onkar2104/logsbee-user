import uuid
from datetime import datetime, timezone

from dateutil.relativedelta import relativedelta
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.security import hash_password, verify_password
from core.user_permissions import (
    check_user_access,
    check_user_role,
    get_user_role,
    is_super_admin,
    check_permission,
)
from models.user_model import User
from repositories.user_repository import UserRepository
from repositories.password_history_repository import PasswordHistoryRepository
from schemas.user_schema import UserCreate, UserUpdate


class UserService:

    @staticmethod
    def create_user(db: Session, data: UserCreate, current_user):
        # Platform Super Admin creates accounts and their first Admin via
        # AccountService. This endpoint is for account Admins only.
        check_permission(current_user, "users.create")
        if current_user.account_id is None:
            raise HTTPException(status_code=403, detail="Account-scoped user creation is required.")

        email = data.email.strip().lower()
        if UserRepository.get_by_email(db, email):
            raise HTTPException(status_code=409, detail="Email already exists")

        role = None
        if data.user_role_id:
            role = UserRepository.get_role_by_id(db, data.user_role_id)
            if role is None:
                raise HTTPException(status_code=400, detail="Invalid or inactive user role.")
            if role.name.strip().lower() == "super admin":
                raise HTTPException(status_code=403, detail="Super Admin cannot be assigned by an Account Admin.")
            if role.account_id not in (None, current_user.account_id):
                raise HTTPException(status_code=403, detail="You cannot assign a role from another account.")
            if role.account_id is None and role.name.strip().lower() != "user":
                raise HTTPException(status_code=403, detail="Only the default User system role can be assigned.")
        else:
            role = UserRepository.get_by_user_role(db, "user")

        if role is None:
            raise HTTPException(status_code=500, detail="Default user role is not configured.")

        user_data = data.model_dump(exclude={"email", "password", "user_role_id"})
        user_data["email"] = email
        user_data["password_hash"] = hash_password(data.password.get_secret_value())
        user_data["user_role_id"] = role.id
        user_data["account_id"] = current_user.account_id
        user_data["created_by"] = current_user.id

        try:
            user = User(**user_data)
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="Email already exists or invalid role.")

    @staticmethod
    def get_users(db: Session, current_user):
        if is_super_admin(current_user):
            return UserRepository.get_all_active(db)
        check_permission(current_user, "users.view")
        return UserRepository.get_all_active(db, account_id=current_user.account_id)

    @staticmethod
    def get_user(db: Session, user_id: uuid.UUID, current_user):
        user = UserRepository.get_by_id(db, user_id)
        if not user or user.is_deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        check_user_access(current_user, user)
        return user

    @staticmethod
    def update_user(db: Session, user_id: uuid.UUID, data: UserUpdate, current_user):
        user = UserService.get_user(db, user_id, current_user)
        if user.id != current_user.id:
            check_permission(current_user, "users.update")
        changes = data.model_dump(exclude_unset=True)

        # A normal user may update their own profile, but cannot change roles.
        if "user_role_id" in changes:
            check_permission(current_user, "users.update")
            if not is_super_admin(current_user) and (
                user.account_id != current_user.account_id
            ):
                raise HTTPException(status_code=403, detail="Cross-account role assignment is forbidden.")
            role_id = changes["user_role_id"]
            if role_id is None:
                raise HTTPException(status_code=400, detail="A user role is required.")
            if role_id is not None:
                role = UserRepository.get_role_by_id(db, role_id)
                if role is None:
                    raise HTTPException(status_code=400, detail="Invalid or inactive user role.")
                if role.name.strip().lower() == "super admin":
                    raise HTTPException(status_code=403, detail="Super Admin cannot be assigned here.")
                if not is_super_admin(current_user) and role.account_id not in (
                    None, current_user.account_id
                ):
                    raise HTTPException(status_code=403, detail="Role belongs to another account.")
                if not is_super_admin(current_user) and role.account_id is None and role.name.strip().lower() != "user":
                    raise HTTPException(status_code=403, detail="This system role cannot be assigned.")

        if changes.get("email") is not None:
            email = changes["email"].strip().lower()
            if email != user.email and UserRepository.email_exists(db, email, user.id):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists.")
            changes["email"] = email

        # Never allow clients to move users between accounts or edit audit ownership.
        forbidden = {"account_id", "created_by", "deleted_by", "is_deleted"}
        if forbidden.intersection(changes):
            raise HTTPException(status_code=400, detail="Protected fields cannot be updated.")

        for field, value in changes.items():
            setattr(user, field, value)
        user.updated_at = datetime.now(timezone.utc)
        user.updated_by = current_user.id

        try:
            db.commit()
            db.refresh(user)
            return user
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="Email already exists or invalid user role.")

    @staticmethod
    def delete_user(db: Session, user_id: uuid.UUID, deleted_by, reason, current_user):
        user = UserService.get_user(db, user_id, current_user)
        if user.id == current_user.id:
            raise HTTPException(status_code=400, detail="You cannot delete your own account.")
        if not is_super_admin(current_user) and current_user.account_id == user.account_id:
            check_permission(current_user, "users.delete")
        elif not is_super_admin(current_user):
            raise HTTPException(status_code=403, detail="Permission denied.")
        user.is_deleted = True
        user.deleted_at = datetime.now(timezone.utc)
        user.deleted_by = current_user.id
        user.deletion_reason = reason
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def change_password(db: Session, request, current_user):
        user = current_user
        if not user or user.is_deleted:
            raise HTTPException(status_code=404, detail="User not found")

        current_password = request.current_password.get_secret_value()
        new_password = request.new_password.get_secret_value()
        if not verify_password(current_password, user.password_hash):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        if verify_password(new_password, user.password_hash):
            raise HTTPException(status_code=400, detail="New password must differ from current password")

        history = PasswordHistoryRepository.get_last_five(db, user.id)
        for record in history:
            if verify_password(new_password, record.password_hash):
                raise HTTPException(status_code=400, detail="You cannot reuse any of your last 5 passwords")

        now = datetime.now(timezone.utc)
        try:
            PasswordHistoryRepository.add(db, user.id, user.password_hash)
            PasswordHistoryRepository.keep_last_five(db, user.id)
            user.password_hash = hash_password(new_password)
            user.password_expires_at = now + relativedelta(months=1)
            user.updated_at = now
            db.commit()
            db.refresh(user)
            return {"message": "Password changed successfully"}
        except Exception:
            db.rollback()
            raise

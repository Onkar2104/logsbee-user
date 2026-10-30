import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.auth_dependencies import get_current_user
from controllers.user_controller import UserController
from schemas.user_schema import (
    UserCreate,
    UserUpdate,
    UserResponse,
)
from schemas.user_schema import PasswordChange
from typing import Optional

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
):
    return UserController.create_user(db, data)


@router.get("/", response_model=list[UserResponse])
def get_users(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return UserController.get_users(db, current_user)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return UserController.get_user(db, user_id, current_user)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return UserController.update_user(db, user_id, data, current_user)


@router.delete("/{user_id}")
def delete_user(
    user_id: uuid.UUID,
    deleted_by: Optional[uuid.UUID] = Query(default=None),
    reason: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    UserController.delete_user(db, user_id, deleted_by, reason, current_user)
    return {"message": "User soft-deleted successfully"}


@router.patch(
    "/{user_id}/password",
    status_code=status.HTTP_200_OK,
)
def change_password(
    user_id: uuid.UUID,
    data: PasswordChange,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    UserController.change_password(db, user_id, data, current_user)

    return {"message": "Password changed successfully"}
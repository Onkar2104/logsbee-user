import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.auth_dependencies import get_current_user
from core.database import get_db
from controllers.user_controller import UserController
from schemas.user_schema import UserCreate, UserUpdate, UserResponse, PasswordChange

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return UserController.create_user(db, data, current_user)


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
    reason: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    UserController.delete_user(db, user_id, None, reason, current_user)
    return {"message": "User soft-deleted successfully"}


@router.post("/change-password")
def change_password(
    request: PasswordChange,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return UserController.change_password(db, request, current_user)

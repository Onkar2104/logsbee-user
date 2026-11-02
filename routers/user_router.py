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


@router.get("/me")
def get_current_user_profile(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return the authenticated user's Logsbee identity and product entitlements."""
    from services.product_service import ProductService

    role = current_user.user_role
    account = current_user.account
    products = ProductService.list_products(db, current_user)

    return {
        "id": str(current_user.id),
        "account_id": str(current_user.account_id) if current_user.account_id else None,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
        "contact": current_user.contact,
        "is_email_verified": current_user.is_email_verified,
        "is_contact_verified": current_user.is_contact_verified,
        "is_two_factor_authenticated": current_user.is_two_factor_authenticated,
        "role": {
            "id": str(role.id),
            "name": role.name,
            "is_system_role": role.is_system_role,
        } if role else None,
        "permission_codes": sorted(permission.code for permission in role.permissions) if role else [],
        "account": {
            "id": str(account.account_id),
            "name": account.name,
            "is_active": account.is_active,
            "is_deleted": account.is_deleted,
        } if account else None,
        "products": [
            {
                "id": str(product.id),
                "code": product.code,
                "name": product.name,
            }
            for product in products
        ],
    }



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

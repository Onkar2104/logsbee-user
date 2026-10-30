from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from controllers.auth_controller import LoginController
from schemas.auth_schema import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
)


router = APIRouter(
    prefix="/api/auth/login",
    tags=["Authentication"],
)


@router.post("/password", response_model=LoginResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    return LoginController.login(db, request)


@router.post("/refresh")
def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    return LoginController.refresh_token(
        db=db,
        refresh_token=request.refresh_token,
    )
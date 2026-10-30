from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from core.database import get_db
from core.limiter import limiter

from controllers.auth_controller import LoginController

from schemas.auth_schema import (
    LoginRequest,
    LoginResponse,
    VerifyLoginOTPRequest,
    RefreshTokenRequest,
)


router = APIRouter(
    prefix="/api/auth/login",
    tags=["Authentication"],
)


@router.post(
    "/password",
    response_model=LoginResponse,
)
@limiter.limit("5/minute")
def login(
    request: Request,
    credentials: LoginRequest,
    db: Session = Depends(get_db),
):

    return LoginController.login(
        db,
        credentials,
    )


@router.post(
    "/verify-otp",
    response_model=LoginResponse,
)
@limiter.limit("5/minute")
def verify_login_otp(
    request: Request,
    credentials: VerifyLoginOTPRequest,
    db: Session = Depends(get_db),
):

    return LoginController.verify_login_otp(
        db,
        credentials,
    )


@router.post("/refresh")
def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
):

    return LoginController.refresh_token(
        db=db,
        refresh_token=request.refresh_token,
    )
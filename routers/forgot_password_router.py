from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from core.database import get_db
from core.limiter import limiter
from controllers.forgot_password_controller import (
    ForgotPasswordController,
)
from schemas.forgot_password_schema import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
)

router = APIRouter(
    prefix="/api/auth/forgot-password",
    tags=["Forgot Password"],
)


@router.post("/send-otp")
@limiter.limit("3/minute")
def send_otp(
    request: Request,
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    return ForgotPasswordController.send_otp(
        db=db,
        email=str(data.email),
    )


@router.post("/reset")
@limiter.limit("5/minute")
def reset_password(
    request: Request,
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    return ForgotPasswordController.reset_password(
        db=db,
        email=str(data.email),
        otp=data.otp,
        new_password=data.new_password.get_secret_value(),
    )

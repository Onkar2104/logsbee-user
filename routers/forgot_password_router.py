from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from controllers.forgot_password_controller import (
    ForgotPasswordController,
)
from schemas.forgot_password_schema import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
)

router = APIRouter(
    prefix="/api/v1/auth/forgot-password",
    tags=["Forgot Password"],
)


@router.post("/send-otp")
def send_otp(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    return ForgotPasswordController.send_otp(
        db=db,
        email=str(data.email),
    )


@router.post("/reset")
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    return ForgotPasswordController.reset_password(
        db=db,
        email=str(data.email),
        otp=data.otp,
        new_password=data.new_password.get_secret_value(),
    )
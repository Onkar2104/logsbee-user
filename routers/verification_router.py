from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from core.database import get_db
from schemas.verification_schema import (
    OTPRequest,
    VerificationResponse,
)
from controllers.verification_controller import VerificationController
from core.auth_dependencies import get_current_user
from services.verification_service import VerificationService

router = APIRouter(
    prefix="/api/users",
    tags=["Verification"],
)


@router.post(
    "/{user_id}/verification/email",
    response_model=VerificationResponse,
)
def email_verification(
    user_id: UUID,
    request: OTPRequest,
    db: Session = Depends(get_db),
):
    if request.otp is None:
        return VerificationController.send_email_otp(
            db, user_id
        )

    return VerificationController.verify_email_otp(
        db, user_id, request.otp
    )


# @router.post(
#     "/{user_id}/verification/whatsapp",
#     response_model=VerificationResponse,
# )
# def whatsapp_verification(
#     user_id: UUID,
#     request: OTPRequest,
#     db: Session = Depends(get_db),
# ):
#     if request.otp is None:
#         return VerificationController.send_whatsapp_otp(
#             db, user_id
#         )

#     return VerificationController.verify_whatsapp_otp(
#         db, user_id, request.otp
#     )


@router.post("/me/two-factor/email")
def manage_two_factor_email(
    request: OTPRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Enroll or verify email-based 2FA for the authenticated user only."""
    if request.otp is None:
        return VerificationService.send_otp(
            db, current_user.id, "email", purpose="two_factor_activation"
        )
    return VerificationService.verify_otp(
        db, current_user.id, "email", request.otp,
        purpose="two_factor_activation",
    )


@router.delete("/me/two-factor")
def disable_two_factor(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    current_user.is_two_factor_authenticated = False
    db.commit()
    return {"message": "Two-factor authentication disabled"}

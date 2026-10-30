from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from core.database import get_db
from schemas.verification_schema import (
    OTPRequest,
    VerificationResponse,
)
from controllers.verification_controller import VerificationController

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
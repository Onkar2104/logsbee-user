from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from uuid import UUID

from core.database import get_db
from core.limiter import limiter
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
@limiter.limit("5/minute")
def email_verification(
    request: Request,
    user_id: UUID,
    otp_request: OTPRequest,
    db: Session = Depends(get_db),
):
    if otp_request.otp is None:
        return VerificationController.send_email_otp(
            db, user_id
        )

    return VerificationController.verify_email_otp(
        db, user_id, otp_request.otp
    )


# @router.post(
#     "/{user_id}/verification/whatsapp",
#     response_model=VerificationResponse,
# )
# def whatsapp_verification(
#     request: Request,
#     user_id: UUID,
#     otp_request: OTPRequest,
#     db: Session = Depends(get_db),
# ):
#     if otp_request.otp is None:
#         return VerificationController.send_whatsapp_otp(
#             db, user_id
#         )
#
#     return VerificationController.verify_whatsapp_otp(
#         db, user_id, otp_request.otp
#     )

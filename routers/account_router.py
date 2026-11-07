from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from controllers.account_controller import AccountController
from core.database import get_db
from core.limiter import limiter
from schemas.account_schema import (
    AccountRegistrationCreate,
    RegistrationResendRequest,
    RegistrationResponse,
)
from schemas.verification_schema import VerificationResponse

router = APIRouter(prefix="/api/accounts", tags=["Accounts"])


@router.post(
    "/register",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("3/hour")
def register_account(
    request: Request,
    data: AccountRegistrationCreate,
    db: Session = Depends(get_db),
):
    return AccountController.register_account(db, data)


@router.post(
    "/register/resend-otp",
    response_model=VerificationResponse,
)
@limiter.limit("3/minute")
def resend_registration_otp(
    request: Request,
    data: RegistrationResendRequest,
    db: Session = Depends(get_db),
):
    return AccountController.resend_registration_otp(db, data.email)

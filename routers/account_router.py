from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from controllers.account_controller import AccountController
from core.auth_dependencies import get_current_user
from core.database import get_db
from core.limiter import limiter
from schemas.account_schema import (
    AccountCreate,
    AccountCreatedResponse,
    AccountRegistrationCreate,
    RegistrationResendRequest,
    RegistrationResponse,
)
from schemas.verification_schema import VerificationResponse

router = APIRouter(prefix="/api/accounts", tags=["Accounts"])


@router.post(
    "/",
    response_model=AccountCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_account(
    data: AccountCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return AccountController.create_account(db, data, current_user)


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

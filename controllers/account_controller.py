from sqlalchemy.orm import Session

from schemas.account_schema import AccountRegistrationCreate
from services.account_registration_service import AccountRegistrationService


class AccountController:
    @staticmethod
    def register_account(db: Session, data: AccountRegistrationCreate):
        return AccountRegistrationService.register_account(db, data)

    @staticmethod
    def resend_registration_otp(db: Session, email: str):
        return AccountRegistrationService.resend_registration_otp(db, email)

from sqlalchemy.orm import Session

from schemas.account_schema import AccountRegistrationCreate
from services.account_registration_service import AccountRegistrationService


class AccountController:
    @staticmethod
    def register_account(db: Session, data: AccountRegistrationCreate):
        return AccountRegistrationService.register_account(db, data)

    @staticmethod
    def verify_account_email(db: Session, account_id, otp: str):
        return AccountRegistrationService.verify_account_email(db, account_id, otp)

    @staticmethod
    def resend_registration_otp(db: Session, account_id, verification_type: str):
        return AccountRegistrationService.resend_registration_otp(
            db, account_id, verification_type
        )

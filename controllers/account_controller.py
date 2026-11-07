from sqlalchemy.orm import Session

from schemas.account_schema import AccountCreate, AccountRegistrationCreate
from services.account_registration_service import AccountRegistrationService
from services.account_service import AccountService


class AccountController:
    @staticmethod
    def create_account(db: Session, data: AccountCreate, current_user):
        return AccountService.create_account_with_admin(db, data, current_user)

    @staticmethod
    def register_account(db: Session, data: AccountRegistrationCreate):
        return AccountRegistrationService.register_account(db, data)

    @staticmethod
    def resend_registration_otp(db: Session, email: str):
        return AccountRegistrationService.resend_registration_otp(db, email)

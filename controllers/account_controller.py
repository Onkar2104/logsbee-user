from sqlalchemy.orm import Session

from schemas.account_schema import AccountCreate
from services.account_service import AccountService


class AccountController:
    @staticmethod
    def create_account(db: Session, data: AccountCreate, current_user):
        return AccountService.create_account_with_admin(
            db, data, current_user
        )

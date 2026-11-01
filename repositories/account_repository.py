from sqlalchemy import select
from sqlalchemy.orm import Session

from models.account_model import Account


class AccountRepository:
    @staticmethod
    def get_by_id(db: Session, account_id):
        return db.scalar(
            select(Account).where(
                Account.account_id == account_id,
                Account.is_deleted.is_(False),
            )
        )

    @staticmethod
    def create(db: Session, account: Account):
        db.add(account)
        db.flush()
        return account

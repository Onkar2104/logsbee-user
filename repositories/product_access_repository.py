from sqlalchemy import select
from sqlalchemy.orm import Session

from models.account_product_model import AccountProduct
from models.user_product_model import UserProduct


class ProductAccessRepository:
    @staticmethod
    def get_account_access(db: Session, account_id):
        return list(db.scalars(select(AccountProduct).where(AccountProduct.account_id == account_id)).all())

    @staticmethod
    def get_user_access(db: Session, user_id):
        return list(db.scalars(select(UserProduct).where(UserProduct.user_id == user_id)).all())

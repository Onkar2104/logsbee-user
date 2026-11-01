from sqlalchemy import select
from sqlalchemy.orm import Session

from models.product_model import Product


class ProductRepository:
    @staticmethod
    def list_all(db: Session, include_inactive: bool = False):
        query = select(Product)
        if not include_inactive:
            query = query.where(Product.is_active.is_(True))
        return list(db.scalars(query.order_by(Product.name)).all())

    @staticmethod
    def get_by_id(db: Session, product_id):
        return db.scalar(select(Product).where(Product.id == product_id))

    @staticmethod
    def get_by_code(db: Session, code: str):
        return db.scalar(select(Product).where(Product.code == code))

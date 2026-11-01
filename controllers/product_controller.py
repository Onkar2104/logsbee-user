from uuid import UUID
from sqlalchemy.orm import Session

from schemas.product_schema import ProductCreate, ProductUpdate
from services.product_service import ProductService
from services.product_access_service import ProductAccessService


class ProductController:
    @staticmethod
    def list_products(db: Session, current_user):
        return ProductService.list_products(db, current_user)

    @staticmethod
    def create_product(db: Session, data: ProductCreate, current_user):
        return ProductService.create_product(db, data, current_user)

    @staticmethod
    def update_product(db: Session, product_id: UUID, data: ProductUpdate, current_user):
        return ProductService.update_product(db, product_id, data, current_user)

    @staticmethod
    def list_account_products(db: Session, account_id: UUID, current_user):
        return ProductAccessService.list_account_products(db, account_id, current_user)

    @staticmethod
    def set_account_products(db: Session, account_id: UUID, product_ids: list[UUID], current_user):
        return ProductAccessService.set_account_products(db, account_id, product_ids, current_user)

    @staticmethod
    def list_user_products(db: Session, user_id: UUID, current_user):
        return ProductAccessService.list_user_products(db, user_id, current_user)

    @staticmethod
    def set_user_products(db: Session, user_id: UUID, product_ids: list[UUID], current_user):
        return ProductAccessService.set_user_products(db, user_id, product_ids, current_user)

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.user_permissions import check_super_admin, is_super_admin, is_account_admin
from models.product_model import Product
from models.account_product_model import AccountProduct
from models.user_product_model import UserProduct
from schemas.product_schema import ProductCreate, ProductUpdate


class ProductService:
    @staticmethod
    def list_products(db: Session, current_user):
        # Platform Super Admin can see the complete product catalogue.
        if is_super_admin(current_user):
            return db.query(Product).order_by(Product.name).all()

        now = datetime.now(timezone.utc)

        # Account Admin sees products enabled for their own account.
        if is_account_admin(current_user):
            return (
                db.query(Product)
                .join(AccountProduct, AccountProduct.product_id == Product.id)
                .filter(
                    AccountProduct.account_id == current_user.account_id,
                    AccountProduct.is_enabled.is_(True),
                    (AccountProduct.expires_at.is_(None) | (AccountProduct.expires_at > now)),
                    Product.is_active.is_(True),
                )
                .order_by(Product.name)
                .all()
            )

        # Standard users see only products explicitly assigned to them,
        # provided the product is also enabled and unexpired for their account.
        if current_user.account_id is None:
            raise HTTPException(status_code=403, detail="Product access is not available.")

        return (
            db.query(Product)
            .join(UserProduct, UserProduct.product_id == Product.id)
            .join(
                AccountProduct,
                (AccountProduct.product_id == Product.id)
                & (AccountProduct.account_id == current_user.account_id),
            )
            .filter(
                UserProduct.user_id == current_user.id,
                UserProduct.is_enabled.is_(True),
                AccountProduct.is_enabled.is_(True),
                (AccountProduct.expires_at.is_(None) | (AccountProduct.expires_at > now)),
                Product.is_active.is_(True),
            )
            .order_by(Product.name)
            .all()
        )

    @staticmethod
    def create_product(db: Session, data: ProductCreate, current_user):
        check_super_admin(current_user)
        if db.query(Product).filter(Product.code == data.code.strip().upper()).first():
            raise HTTPException(status_code=409, detail="Product code already exists.")
        product = Product(code=data.code.strip().upper(), name=data.name.strip(), description=data.description)
        db.add(product)
        try:
            db.commit()
            db.refresh(product)
            return product
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="Product code already exists.")

    @staticmethod
    def update_product(db: Session, product_id: UUID, data: ProductUpdate, current_user):
        check_super_admin(current_user)
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(product, key, value)
        product.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(product)
        return product

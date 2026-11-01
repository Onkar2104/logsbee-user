from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.user_permissions import check_super_admin
from models.product_model import Product
from schemas.product_schema import ProductCreate, ProductUpdate


class ProductService:
    @staticmethod
    def list_products(db: Session, current_user):
        check_super_admin(current_user)
        return db.query(Product).order_by(Product.name).all()

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

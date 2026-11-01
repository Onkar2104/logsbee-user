from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.user_permissions import check_super_admin, check_user_role
from models.account_model import Account
from models.account_product_model import AccountProduct
from models.product_model import Product
from models.user_model import User
from models.user_product_model import UserProduct


class ProductAccessService:
    @staticmethod
    def list_account_products(db: Session, account_id: UUID, current_user):
        check_super_admin(current_user)
        rows = db.query(AccountProduct, Product).join(
            Product, Product.id == AccountProduct.product_id
        ).filter(AccountProduct.account_id == account_id).all()

        # SQLAlchemy returns (AccountProduct, Product) tuples for this query.
        # Convert them to plain dictionaries so FastAPI can serialize the response.
        return [
            {
                "product_id": account_product.product_id,
                "code": product.code,
                "name": product.name,
                "is_enabled": account_product.is_enabled,
                "expires_at": account_product.expires_at,
            }
            for account_product, product in rows
        ]

    @staticmethod
    def set_account_products(db: Session, account_id: UUID, product_ids: list[UUID], current_user):
        check_super_admin(current_user)
        account = db.query(Account).filter(Account.account_id == account_id, Account.is_deleted.is_(False)).first()
        if not account:
            raise HTTPException(status_code=404, detail="Account not found.")
        products = db.query(Product).filter(Product.id.in_(set(product_ids)), Product.is_active.is_(True)).all() if product_ids else []
        if len(products) != len(set(product_ids)):
            raise HTTPException(status_code=400, detail="One or more products are invalid or inactive.")
        db.query(AccountProduct).filter(AccountProduct.account_id == account_id).delete(synchronize_session=False)
        for product in products:
            db.add(AccountProduct(account_id=account_id, product_id=product.id, is_enabled=True, created_by=current_user.id))
        db.commit()
        return {"message": "Account product access updated.", "enabled_product_count": len(products)}

    @staticmethod
    def list_user_products(db: Session, user_id: UUID, current_user):
        check_user_role(current_user)
        if current_user.account_id is None:
            raise HTTPException(status_code=400, detail="Use account-scoped user management.")
        user = db.query(User).filter(User.id == user_id, User.account_id == current_user.account_id, User.is_deleted.is_(False)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found in your account.")
        rows = db.query(UserProduct, Product).join(
            Product, Product.id == UserProduct.product_id
        ).filter(UserProduct.user_id == user_id).all()

        # Convert (UserProduct, Product) tuples into JSON-compatible dictionaries.
        return [
            {
                "product_id": user_product.product_id,
                "code": product.code,
                "name": product.name,
                "is_enabled": user_product.is_enabled,
            }
            for user_product, product in rows
        ]

    @staticmethod
    def set_user_products(db: Session, user_id: UUID, product_ids: list[UUID], current_user):
        check_user_role(current_user)
        if current_user.account_id is None:
            raise HTTPException(status_code=400, detail="Use account-scoped user management.")
        user = db.query(User).filter(User.id == user_id, User.account_id == current_user.account_id, User.is_deleted.is_(False)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found in your account.")
        ids = set(product_ids)
        enabled_account_products = db.query(AccountProduct.product_id).join(Product, Product.id == AccountProduct.product_id).filter(
            AccountProduct.account_id == current_user.account_id,
            AccountProduct.is_enabled.is_(True),
            (AccountProduct.expires_at.is_(None) | (AccountProduct.expires_at > datetime.now(timezone.utc))),
            Product.is_active.is_(True),
        ).all()
        allowed = {row[0] for row in enabled_account_products}
        if not ids.issubset(allowed):
            raise HTTPException(status_code=400, detail="Users can only receive products enabled for their account.")
        db.query(UserProduct).filter(UserProduct.user_id == user_id).delete(synchronize_session=False)
        for product_id in ids:
            db.add(UserProduct(user_id=user_id, product_id=product_id, is_enabled=True, granted_by=current_user.id))
        db.commit()
        return {"message": "User product access updated.", "enabled_product_count": len(ids)}

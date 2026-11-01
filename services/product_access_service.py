from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.user_permissions import (
    check_super_admin,
    check_user_role,
    is_super_admin,
    is_account_admin,
)
from models.account_model import Account
from models.account_product_model import AccountProduct
from models.product_model import Product
from models.user_model import User
from models.user_product_model import UserProduct


class ProductAccessService:
    @staticmethod
    def list_account_products(db: Session, account_id: UUID, current_user):
        # Account Admins may only view the products purchased/enabled for
        # their own account. Never trust the account_id supplied by the client.
        if is_account_admin(current_user):
            if current_user.account_id != account_id:
                raise HTTPException(status_code=404, detail="Account not found.")

            now = datetime.utcnow()
            rows = db.query(AccountProduct, Product).join(
                Product, Product.id == AccountProduct.product_id
            ).filter(
                AccountProduct.account_id == current_user.account_id,
                AccountProduct.is_enabled.is_(True),
                (AccountProduct.expires_at.is_(None) | (AccountProduct.expires_at > now)),
                Product.is_active.is_(True),
            ).order_by(Product.name).all()

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

        # Platform Super Admin sees the complete product catalogue for the
        # requested account, including products not currently enabled there.
        check_super_admin(current_user)
        account = db.query(Account).filter(
            Account.account_id == account_id,
            Account.is_deleted.is_(False),
        ).first()
        if account is None:
            raise HTTPException(status_code=404, detail="Account not found.")

        rows = db.query(Product, AccountProduct).outerjoin(
            AccountProduct,
            (AccountProduct.product_id == Product.id)
            & (AccountProduct.account_id == account_id),
        ).order_by(Product.name).all()

        return [
            {
                "product_id": product.id,
                "code": product.code,
                "name": product.name,
                "is_enabled": bool(account_product and account_product.is_enabled),
                "expires_at": account_product.expires_at if account_product else None,
            }
            for product, account_product in rows
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
        # Fetch by user UUID first, then enforce tenant ownership separately.
        # This keeps the lookup behavior clear while preserving cross-account isolation.
        user = db.query(User).filter(
            User.id == user_id,
            User.is_deleted.is_(False),
        ).first()
        if user is None or user.account_id != current_user.account_id:
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

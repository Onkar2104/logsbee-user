from datetime import datetime, timezone

from fastapi import HTTPException

from models.account_product_model import AccountProduct
from models.product_model import Product
from models.user_product_model import UserProduct


def require_product_access(db, current_user, product_code: str):
    """Require the product to be active globally and enabled for the user's account."""
    if current_user.account_id is None:
        return True  # Platform Super Admin is not an account tenant.
    product = db.query(Product).filter(Product.code == product_code, Product.is_active.is_(True)).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found or inactive.")
    assignment = db.query(AccountProduct).filter(
        AccountProduct.account_id == current_user.account_id,
        AccountProduct.product_id == product.id,
        AccountProduct.is_enabled.is_(True),
    ).first()
    if assignment is None or (assignment.expires_at and assignment.expires_at <= datetime.now(timezone.utc)):
        raise HTTPException(status_code=403, detail="This product is not enabled for your account.")
    return True


def require_user_product_access(db, current_user, product_code: str):
    """Require both account-level and individual-user product assignment."""
    require_product_access(db, current_user, product_code)
    if current_user.account_id is None:
        return True
    product = db.query(Product).filter(Product.code == product_code, Product.is_active.is_(True)).first()
    assignment = db.query(UserProduct).filter(
        UserProduct.user_id == current_user.id,
        UserProduct.product_id == product.id,
        UserProduct.is_enabled.is_(True),
    ).first()
    if assignment is None:
        raise HTTPException(status_code=403, detail="You do not have access to this product.")
    return True

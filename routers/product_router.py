import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from controllers.product_controller import ProductController
from core.auth_dependencies import get_current_user
from core.database import get_db
from schemas.product_schema import (\n    ProductCreate, ProductUpdate, ProductResponse, ProductAssignment,\n    AccountProductResponse, UserProductResponse,\n)

router = APIRouter(prefix="/api/products", tags=["Products"])


@router.get("/", response_model=list[ProductResponse])
def list_products(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return ProductController.list_products(db, current_user)


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return ProductController.create_product(db, data, current_user)


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(product_id: uuid.UUID, data: ProductUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return ProductController.update_product(db, product_id, data, current_user)


@router.get("/accounts/{account_id}", response_model=list[AccountProductResponse])
def list_account_products(account_id: uuid.UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return ProductController.list_account_products(db, account_id, current_user)


@router.put("/accounts/{account_id}")
def set_account_products(account_id: uuid.UUID, data: ProductAssignment, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return ProductController.set_account_products(db, account_id, data.product_ids, current_user)


@router.get("/users/{user_id}", response_model=list[UserProductResponse])
def list_user_products(user_id: uuid.UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return ProductController.list_user_products(db, user_id, current_user)


@router.put("/users/{user_id}")
def set_user_products(user_id: uuid.UUID, data: ProductAssignment, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return ProductController.set_user_products(db, user_id, data.product_ids, current_user)

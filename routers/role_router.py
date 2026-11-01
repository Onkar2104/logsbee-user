import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from controllers.role_controller import RoleController
from core.auth_dependencies import get_current_user
from core.database import get_db
from schemas.role_schema import RoleCreate, RoleUpdate, RoleResponse, PermissionResponse

router = APIRouter(prefix="/api/roles", tags=["Roles"])


@router.get("/", response_model=list[RoleResponse])
def list_roles(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return RoleController.list_roles(db, current_user)


@router.get("/permissions", response_model=list[PermissionResponse])
def list_permissions(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return RoleController.list_permissions(db, current_user)


@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(data: RoleCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return RoleController.create_role(db, data, current_user)


@router.patch("/{role_id}", response_model=RoleResponse)
def update_role(role_id: uuid.UUID, data: RoleUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return RoleController.update_role(db, role_id, data, current_user)


@router.delete("/{role_id}")
def delete_role(role_id: uuid.UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return RoleController.delete_role(db, role_id, current_user)

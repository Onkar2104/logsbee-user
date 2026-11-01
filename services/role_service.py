import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.user_permissions import check_super_admin, is_super_admin, is_account_admin
from models.user_role_model import UserRole
from repositories.permission_repository import PermissionRepository
from repositories.role_repository import RoleRepository
from schemas.role_schema import RoleCreate, RoleUpdate


class RoleService:
    @staticmethod
    def _require_account_admin(current_user):
        if not is_account_admin(current_user):
            raise HTTPException(status_code=403, detail="Account Admin access required.")

    @staticmethod
    def list_roles(db: Session, current_user):
        if is_super_admin(current_user):
            return list(db.query(UserRole).filter(
                UserRole.account_id.is_(None),
                UserRole.is_system_role.is_(True),
                UserRole.is_deleted.is_(False),
            ).all())
        RoleService._require_account_admin(current_user)
        return RoleRepository.get_account_roles(db, current_user.account_id)

    @staticmethod
    def list_permissions(db: Session, current_user):
        if not (is_super_admin(current_user) or is_account_admin(current_user)):
            raise HTTPException(status_code=403, detail="Permission denied.")
        return PermissionRepository.get_all(db)

    @staticmethod
    def create_role(db: Session, data: RoleCreate, current_user):
        RoleService._require_account_admin(current_user)
        name = data.name.strip()
        if RoleRepository.get_by_name(db, current_user.account_id, name):
            raise HTTPException(status_code=409, detail="A role with this name already exists.")

        codes = list(dict.fromkeys(data.permission_codes))
        permissions = PermissionRepository.get_by_codes(db, codes)
        found = {p.code for p in permissions}
        missing = sorted(set(codes) - found)
        if missing:
            raise HTTPException(status_code=400, detail={"unknown_permission_codes": missing})

        role = UserRole(
            account_id=current_user.account_id,
            name=name,
            description=data.description,
            is_system_role=False,
            permissions=permissions,
        )
        try:
            db.add(role)
            db.commit()
            db.refresh(role)
            return role
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="Role name already exists.")

    @staticmethod
    def update_role(db: Session, role_id: uuid.UUID, data: RoleUpdate, current_user):
        RoleService._require_account_admin(current_user)
        role = RoleRepository.get_by_id(db, role_id)
        if not role or role.account_id != current_user.account_id or role.is_system_role:
            raise HTTPException(status_code=404, detail="Custom role not found.")

        changes = data.model_dump(exclude_unset=True)
        if "name" in changes and changes["name"] is not None:
            name = changes["name"].strip()
            duplicate = RoleRepository.get_by_name(db, current_user.account_id, name)
            if duplicate and duplicate.id != role.id:
                raise HTTPException(status_code=409, detail="A role with this name already exists.")
            role.name = name
        if "description" in changes:
            role.description = changes["description"]
        if "permission_codes" in changes and changes["permission_codes"] is not None:
            codes = list(dict.fromkeys(changes["permission_codes"]))
            permissions = PermissionRepository.get_by_codes(db, codes)
            found = {p.code for p in permissions}
            missing = sorted(set(codes) - found)
            if missing:
                raise HTTPException(status_code=400, detail={"unknown_permission_codes": missing})
            role.permissions = permissions

        role.updated_at = datetime.now(timezone.utc)
        try:
            db.commit()
            db.refresh(role)
            return role
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="Role name already exists.")

    @staticmethod
    def delete_role(db: Session, role_id: uuid.UUID, current_user):
        RoleService._require_account_admin(current_user)
        role = RoleRepository.get_by_id(db, role_id)
        if not role or role.account_id != current_user.account_id or role.is_system_role:
            raise HTTPException(status_code=404, detail="Custom role not found.")
        if role.users:
            raise HTTPException(
                status_code=409,
                detail="This role is assigned to users. Reassign those users before deleting it.",
            )
        role.is_deleted = True
        role.permissions = []
        role.updated_at = datetime.now(timezone.utc)
        db.commit()
        return {"message": "Role deleted successfully."}

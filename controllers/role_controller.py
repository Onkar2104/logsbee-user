import uuid
from sqlalchemy.orm import Session

from schemas.role_schema import RoleCreate, RoleUpdate
from services.role_service import RoleService


class RoleController:
    @staticmethod
    def list_roles(db: Session, current_user):
        return RoleService.list_roles(db, current_user)

    @staticmethod
    def list_permissions(db: Session, current_user):
        return RoleService.list_permissions(db, current_user)

    @staticmethod
    def create_role(db: Session, data: RoleCreate, current_user):
        return RoleService.create_role(db, data, current_user)

    @staticmethod
    def update_role(db: Session, role_id: uuid.UUID, data: RoleUpdate, current_user):
        return RoleService.update_role(db, role_id, data, current_user)

    @staticmethod
    def delete_role(db: Session, role_id: uuid.UUID, current_user):
        return RoleService.delete_role(db, role_id, current_user)

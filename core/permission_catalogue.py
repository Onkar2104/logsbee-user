from sqlalchemy import select

from core.database import SessionLocal
from models.permission_model import Permission


PERMISSIONS = [
    ("users.view", "View users", "View users belonging to the account."),
    ("users.create", "Create users", "Create users in the account."),
    ("users.update", "Update users", "Update users in the account."),
    ("users.delete", "Delete users", "Soft-delete users in the account."),
    ("roles.view", "View roles", "View account roles and their permissions."),
    ("roles.manage", "Manage roles", "Create, update, and delete account roles."),
]


def seed_permissions() -> None:
    with SessionLocal() as db:
        for code, name, description in PERMISSIONS:
            permission = db.scalar(select(Permission).where(Permission.code == code))
            if permission is None:
                db.add(Permission(code=code, name=name, description=description))
            else:
                permission.name = name
                permission.description = description
        db.commit()

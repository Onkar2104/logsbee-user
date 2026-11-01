from sqlalchemy import select

from core.database import SessionLocal
from models.user_role_model import UserRole


DEFAULT_ROLES = [
    {
        "name": "Super admin",
        "description": "Highest-level system administration role.",
    },
    {
        "name": "admin",
        "description": "Administrator responsible for managing one account.",
    },
    {
        "name": "user",
        "description": "Default role assigned to account users.",
    },
]


def seed_roles() -> None:
    with SessionLocal() as db:
        for role_data in DEFAULT_ROLES:
            existing_role = db.scalar(
                select(UserRole).where(
                    UserRole.name == role_data["name"],
                    UserRole.account_id.is_(None),
                )
            )
            if existing_role is None:
                db.add(UserRole(**role_data, is_system_role=True))
            elif not existing_role.is_system_role:
                existing_role.is_system_role = True
        db.commit()

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
        "description": "Administrator responsible for managing users and resources.",
    },
    {
        "name": "user",
        "description": "Default role assigned to newly registered users.",
    },
]


def seed_roles() -> None:
    with SessionLocal() as db:
        for role_data in DEFAULT_ROLES:
            existing_role = db.scalar(
                select(UserRole).where(
                    UserRole.name == role_data["name"]
                )
            )

            if existing_role is None:
                db.add(UserRole(**role_data))

        db.commit()

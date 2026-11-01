from sqlalchemy import select
from sqlalchemy.orm import Session

from models.permission_model import Permission


class PermissionRepository:
    @staticmethod
    def get_all(db: Session):
        return list(db.scalars(select(Permission).order_by(Permission.code)).all())

    @staticmethod
    def get_by_codes(db: Session, codes: list[str]):
        return list(db.scalars(select(Permission).where(Permission.code.in_(codes))).all())

    @staticmethod
    def get_by_code(db: Session, code: str):
        return db.scalar(select(Permission).where(Permission.code == code))

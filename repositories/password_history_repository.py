from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from models.password_history_model import PasswordHistory


class PasswordHistoryRepository:

    @staticmethod
    def get_last_five(db: Session, user_id):
        statement = (
            select(PasswordHistory)
            .where(PasswordHistory.user_id == user_id)
            .order_by(PasswordHistory.created_at.desc())
            .limit(5)
        )
        return list(db.scalars(statement).all())

    @staticmethod
    def add(db: Session, user_id, password_hash: str):
        record = PasswordHistory(
            user_id=user_id,
            password_hash=password_hash,
        )
        db.add(record)
        db.flush()
        return record

    @staticmethod
    def keep_last_five(db: Session, user_id):
        statement = (
            select(PasswordHistory.id)
            .where(PasswordHistory.user_id == user_id)
            .order_by(PasswordHistory.created_at.desc())
            .offset(5)
        )
        old_ids = list(db.scalars(statement).all())

        if old_ids:
            db.execute(
                delete(PasswordHistory).where(
                    PasswordHistory.id.in_(old_ids)
                )
            )
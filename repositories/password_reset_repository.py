from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from models.password_reset_otp_model import PasswordResetOTP


class PasswordResetRepository:

    @staticmethod
    def get_latest(db: Session, user_id):
        statement = (
            select(PasswordResetOTP)
            .where(PasswordResetOTP.user_id == user_id)
            .order_by(PasswordResetOTP.created_at.desc())
            .limit(1)
        )
        return db.scalars(statement).first()

    @staticmethod
    def invalidate_pending(db: Session, user_id):
        statement = (
            update(PasswordResetOTP)
            .where(
                PasswordResetOTP.user_id == user_id,
                PasswordResetOTP.consumed_at.is_(None),
            )
            .values(consumed_at=datetime.utcnow())
        )
        db.execute(statement)

    @staticmethod
    def create(db: Session, record: PasswordResetOTP):
        db.add(record)
        db.flush()
        return record

    @staticmethod
    def save(db: Session, record: PasswordResetOTP):
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
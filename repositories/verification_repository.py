
import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from models.otp_verification_model import VerificationOTP


class VerificationRepository:

    @staticmethod
    def get_latest(
        db: Session,
        user_id: uuid.UUID,
        channel: str,
    ):
        return db.scalar(
            select(VerificationOTP)
            .where(
                VerificationOTP.user_id == user_id,
                VerificationOTP.channel == channel,
            )
            .order_by(VerificationOTP.created_at.desc())
            .limit(1)
        )

    @staticmethod
    def revoke_pending(
        db: Session,
        user_id: uuid.UUID,
        channel: str,
        now: datetime,
    ) -> None:
        db.execute(
            update(VerificationOTP)
            .where(
                VerificationOTP.user_id == user_id,
                VerificationOTP.channel == channel,
                VerificationOTP.consumed_at.is_(None),
            )
            .values(consumed_at=now)
        )
        db.flush()

    @staticmethod
    def create(db: Session, record: VerificationOTP):
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def save(db: Session, record: VerificationOTP):
        db.commit()
        db.refresh(record)
        return record


import uuid

from sqlalchemy.orm import Session

from services.verification_service import VerificationService


class VerificationController:

    @staticmethod
    def send_email_otp(db: Session, user_id: uuid.UUID):
        return VerificationService.send_otp(
            db, user_id, "email"
        )

    @staticmethod
    def verify_email_otp(
        db: Session,
        user_id: uuid.UUID,
        otp: str,
    ):
        return VerificationService.verify_otp(
            db, user_id, "email", otp
        )

    @staticmethod
    def send_whatsapp_otp(
        db: Session,
        user_id: uuid.UUID,
    ):
        return VerificationService.send_otp(
            db, user_id, "whatsapp"
        )

    @staticmethod
    def verify_whatsapp_otp(
        db: Session,
        user_id: uuid.UUID,
        otp: str,
    ):
        return VerificationService.verify_otp(
            db, user_id, "whatsapp", otp
        )

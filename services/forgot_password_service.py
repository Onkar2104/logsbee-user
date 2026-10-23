import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.config import settings
from core.security import hash_password, verify_password
from models.password_reset_otp_model import PasswordResetOTP
from repositories.user_repository import UserRepository
from repositories.password_reset_repository import PasswordResetRepository
from repositories.password_history_repository import PasswordHistoryRepository
from providers.email_provider import EmailProvider


class ForgotPasswordService:

    @staticmethod
    def _hash_otp(user_id, otp: str) -> str:
        message = f"{user_id}:password_reset:{otp}"
        return hmac.new(
            settings.otp_hash_secret.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def send_otp(db: Session, email: str):
        generic_response = {
            "message": (
                "If an account exists for this email, "
                "a password reset OTP will be sent."
            )
        }

        user = UserRepository.get_by_email(db, email)

        if not user or user.is_deleted:
            return generic_response

        now = datetime.utcnow()

        latest = PasswordResetRepository.get_latest(db, user.id)

        if latest and (
            now - latest.created_at.replace(tzinfo=None)
        ).total_seconds() < settings.otp_resend_cooldown_seconds:
            return generic_response

        otp = f"{secrets.randbelow(1_000_000):06d}"

        record = PasswordResetOTP(
            user_id=user.id,
            otp_hash=ForgotPasswordService._hash_otp(
                user.id, otp
            ),
            created_at=now,
            expires_at=now + timedelta(
                seconds=settings.otp_expiry_seconds
            ),
            attempts=0,
        )

        try:
            PasswordResetRepository.invalidate_pending(db, user.id)
            PasswordResetRepository.create(db, record)
            db.commit()
        except Exception:
            db.rollback()
            raise

        try:
            EmailProvider.send_otp(user.email, otp)
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=503,
                detail="Unable to send the reset email. Please try again.",
            )

        return generic_response

    @staticmethod
    def reset_password(
        db: Session,
        email: str,
        otp: str,
        new_password: str,
    ):
        user = UserRepository.get_by_email(db, email)

        if not user or user.is_deleted:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired OTP",
            )

        now = datetime.utcnow()

        try:
            record = (
                db.query(PasswordResetOTP)
                .filter(
                    PasswordResetOTP.user_id == user.id,
                    PasswordResetOTP.consumed_at.is_(None),
                )
                .order_by(PasswordResetOTP.created_at.desc())
                .with_for_update()
                .first()
            )

            if (
                not record
                or record.expires_at.replace(tzinfo=None) <= now
                or record.attempts >= settings.otp_max_attempts
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid or expired OTP",
                )

            submitted_hash = ForgotPasswordService._hash_otp(
                user.id, otp
            )

            if not hmac.compare_digest(
                record.otp_hash, submitted_hash
            ):
                record.attempts += 1
                db.commit()
                raise HTTPException(
                    status_code=400,
                    detail="Invalid or expired OTP",
                )

            if verify_password(new_password, user.password_hash):
                raise HTTPException(
                    status_code=400,
                    detail="New password must differ from the current password",
                )

            history = PasswordHistoryRepository.get_last_five(
                db, user.id
            )

            for old_password in history:
                if verify_password(
                    new_password, old_password.password_hash
                ):
                    raise HTTPException(
                        status_code=400,
                        detail="You cannot reuse any of your last 5 passwords",
                    )

            PasswordHistoryRepository.add(
                db, user.id, user.password_hash
            )

            PasswordHistoryRepository.keep_last_five(
                db, user.id
            )

            user.password_hash = hash_password(new_password)
            user.password_expires_at = now + relativedelta(
                months=1
            )

            record.consumed_at = now

            db.commit()

            return {
                "message": "Password reset successfully. Please log in with your new password."
            }

        except HTTPException:
            raise
        except Exception:
            db.rollback()
            raise
import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.config import settings
from models.otp_verification_model import VerificationOTP
from providers.email_provider import EmailProvider
# from providers.whatsapp_provider import WhatsAppProvider
from repositories.user_repository import UserRepository
from repositories.verification_repository import VerificationRepository


def utc_now() -> datetime:
    # MySQL DATETIME stores naive timestamps; keep all values in UTC.
    return datetime.now(timezone.utc).replace(tzinfo=None)


class VerificationService:

    @staticmethod
    def _hash_otp(
        user_id: uuid.UUID,
        channel: str,
        otp: str,
    ) -> str:
        if len(settings.otp_hash_secret) < 32:
            raise HTTPException(
                status_code=500,
                detail="OTP security is not configured",
            )

        message = f"{user_id}:{channel}:{otp}".encode()

        return hmac.new(
            settings.otp_hash_secret.encode(),
            message,
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def _get_user(db: Session, user_id: uuid.UUID):
        user = UserRepository.get_by_id(db, user_id)

        if user is None or user.is_deleted:
            raise HTTPException(
                status_code=404,
                detail="User not found",
            )

        return user

    @staticmethod
    def send_otp(
        db: Session,
        user_id: uuid.UUID,
        channel: str,
    ):
        user = VerificationService._get_user(db, user_id)

        if channel == "email":
            if user.is_email_verified:
                raise HTTPException(
                    status_code=400,
                    detail="Email is already verified",
                )
            destination = user.email
        elif channel == "whatsapp":
            if user.is_contact_verified:
                raise HTTPException(
                    status_code=400,
                    detail="Phone number is already verified",
                )
            if not user.contact:
                raise HTTPException(
                    status_code=400,
                    detail="User has no phone number",
                )
            destination = user.contact
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported verification channel",
            )

        now = utc_now()

        latest = VerificationRepository.get_latest(
            db, user_id, channel
        )

        if latest is not None:
            cooldown_end = latest.created_at + timedelta(
                seconds=settings.otp_resend_cooldown_seconds
            )
            if now < cooldown_end:
                raise HTTPException(
                    status_code=429,
                    detail="Please wait before requesting another OTP",
                )

        otp = f"{secrets.randbelow(1_000_000):06d}"

        record = VerificationOTP(
            user_id=user_id,
            channel=channel,
            otp_hash=VerificationService._hash_otp(
                user_id, channel, otp
            ),
            created_at=now,
            expires_at=now + timedelta(
                seconds=settings.otp_expiry_seconds
            ),
            attempts=0,
        )

        VerificationRepository.revoke_pending(
            db, user_id, channel, now
        )
        VerificationRepository.create(db, record)

        try:
            if channel == "email":
                EmailProvider.send_otp(destination, otp)
            # else:
            #     WhatsAppProvider.send_otp(destination, otp)
        except Exception:
            # Prevent a code from being used if delivery failed.
            record.consumed_at = utc_now()
            VerificationRepository.save(db, record)

            raise HTTPException(
                status_code=502,
                detail="Could not send verification code",
            ) from None

        return {
            "message": f"Verification code sent via {channel}"
        }

    @staticmethod
    def verify_otp(
        db: Session,
        user_id: uuid.UUID,
        channel: str,
        otp: str,
    ):
        user = VerificationService._get_user(db, user_id)

        flag = (
            "is_email_verified"
            if channel == "email"
            else "is_contact_verified"
        )

        if getattr(user, flag):
            return {"message": "Already verified"}

        record = VerificationRepository.get_latest(
            db, user_id, channel
        )

        if record is None or record.consumed_at is not None:
            raise HTTPException(
                status_code=400,
                detail="No active OTP. Request a new code",
            )

        now = utc_now()

        if now >= record.expires_at:
            record.consumed_at = now
            VerificationRepository.save(db, record)
            raise HTTPException(
                status_code=400,
                detail="OTP has expired. Request a new code",
            )

        if record.attempts >= settings.otp_max_attempts:
            record.consumed_at = now
            VerificationRepository.save(db, record)
            raise HTTPException(
                status_code=429,
                detail="Maximum attempts reached. Request a new code",
            )

        expected_hash = VerificationService._hash_otp(
            user_id, channel, otp
        )

        if not hmac.compare_digest(
            expected_hash, record.otp_hash
        ):
            record.attempts += 1

            if record.attempts >= settings.otp_max_attempts:
                record.consumed_at = now

            VerificationRepository.save(db, record)

            raise HTTPException(
                status_code=400,
                detail="Invalid OTP",
            )

        record.consumed_at = now
        setattr(user, flag, True)

        VerificationRepository.save(db, record)

        return {"message": f"{channel} verification successful"}

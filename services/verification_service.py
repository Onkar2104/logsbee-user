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
    # MySQL DATETIME stores naive timestamps.
    # All timestamps are maintained in UTC.
    return datetime.now(timezone.utc).replace(tzinfo=None)


class VerificationService:

    ALLOWED_PURPOSES = {
        "email": {"email_verification", "login_2fa"},
        "whatsapp": {"phone_verification"},
    }

   

    @staticmethod
    def _hash_otp(
        user_id: uuid.UUID,
        channel: str,
        otp: str,
        purpose: str,
    ) -> str:

        if len(settings.otp_hash_secret) < 32:
            raise HTTPException(
                status_code=500,
                detail="OTP security is not configured",
            )

        message = (
            f"{user_id}:{channel}:{purpose}:{otp}"
        ).encode()

        return hmac.new(
            settings.otp_hash_secret.encode(),
            message,
            hashlib.sha256,
        ).hexdigest()

   

    @staticmethod
    def _get_user(
        db: Session,
        user_id: uuid.UUID,
    ):

        user = UserRepository.get_by_id(db, user_id)

        if user is None or user.is_deleted:
            raise HTTPException(
                status_code=404,
                detail="User not found",
            )

        return user


    @staticmethod
    def _validate_purpose(
        channel: str,
        purpose: str,
    ):

        allowed = VerificationService.ALLOWED_PURPOSES.get(
            channel,
            set(),
        )

        if purpose not in allowed:
            raise HTTPException(
                status_code=400,
                detail="Invalid verification purpose",
            )

  

    @staticmethod
    def send_otp(
        db: Session,
        user_id: uuid.UUID,
        channel: str,
        purpose: str = "email_verification",
    ):

        VerificationService._validate_purpose(
            channel,
            purpose,
        )

        user = VerificationService._get_user(
            db,
            user_id,
        )

    
        if channel == "email":

            if (
                purpose == "email_verification"
                and user.is_email_verified
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Email is already verified",
                )

            if (
                purpose == "login_2fa"
                and not user.is_email_verified
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Please verify your email first",
                )

            destination = user.email

        elif channel == "whatsapp":

            if (
                purpose == "phone_verification"
                and user.is_contact_verified
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Phone number is already verified",
                )
            
            if (
                purpose == "login_2fa"
                and not user.is_contact_verified
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Please verify your contact first",
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
            db,
            user_id,
            channel,
            purpose,
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
            purpose=purpose,
            otp_hash=VerificationService._hash_otp(
                user_id,
                channel,
                otp,
                purpose,
            ),
            created_at=now,
            expires_at=now + timedelta(
                seconds=settings.otp_expiry_seconds
            ),
            attempts=0,
        )

        try:

            VerificationRepository.revoke_pending(
                db,
                user_id,
                channel,
                now,
                purpose,
            )

            VerificationRepository.create(
                db,
                record,
            )

         
            db.commit()
            db.refresh(record)

        except Exception:

            db.rollback()
            raise

      
        try:

            if channel == "email":

                EmailProvider.send_otp(
                    destination,
                    otp,
                )

            # elif channel == "whatsapp":
            #     WhatsAppProvider.send_otp(
            #         destination,
            #         otp,
            #     )

        except Exception:

            try:
                record.consumed_at = utc_now()

                VerificationRepository.save(
                    db,
                    record,
                )

                db.commit()

            except Exception:
                db.rollback()

            raise HTTPException(
                status_code=502,
                detail="Could not send verification code",
            ) from None

    
        if purpose == "login_2fa":

            return {
                "requires_2fa": True,
                "challenge_id": str(record.id),
                "message": "OTP sent to your registered {channel} address",
            }

        return {
            "message": f"Verification code sent via {channel}"
        }



    @staticmethod
    def verify_otp(
        db: Session,
        user_id: uuid.UUID,
        channel: str,
        otp: str,
        purpose: str = "email_verification",
        challenge_id: uuid.UUID | None = None,
    ):

        VerificationService._validate_purpose(
            channel,
            purpose,
        )

        user = VerificationService._get_user(
            db,
            user_id,
        )

  
        if purpose == "email_verification":

            if user.is_email_verified:
                return {"message": "Already verified"}

        elif purpose == "phone_verification":

            if user.is_contact_verified:
                return {"message": "Already verified"}

        elif purpose == "login_2fa":

            if not user.is_two_factor_authenticated:
                raise HTTPException(
                    status_code=400,
                    detail="Two-factor authentication is not enabled",
                )

            if not user.is_email_verified:
                raise HTTPException(
                    status_code=403,
                    detail="Email is not verified",
                )


        now = utc_now()

        try:

        
            if challenge_id is not None:

                record = VerificationRepository.get_by_id(
                    db=db,
                    challenge_id=challenge_id,
                    purpose=purpose,
                    channel=channel,
                )

                if (
                    record is None
                    or record.user_id != user_id
                ):
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid or expired OTP",
                    )

            else:

                record = VerificationRepository.get_latest(
                    db,
                    user_id,
                    channel,
                    purpose,
                )

            if (
                record is None
                or record.consumed_at is not None
            ):
                raise HTTPException(
                    status_code=400,
                    detail="No active OTP. Request a new code",
                )

            
            if now >= record.expires_at:

                record.consumed_at = now

                VerificationRepository.save(
                    db,
                    record,
                )

                db.commit()

                raise HTTPException(
                    status_code=400,
                    detail="OTP has expired. Request a new code",
                )

          
            if record.attempts >= settings.otp_max_attempts:

                record.consumed_at = now

                VerificationRepository.save(
                    db,
                    record,
                )

                db.commit()

                raise HTTPException(
                    status_code=429,
                    detail="Maximum attempts reached. Request a new code",
                )

           
            expected_hash = VerificationService._hash_otp(
                user_id,
                channel,
                otp,
                purpose,
            )

            if not hmac.compare_digest(
                expected_hash,
                record.otp_hash,
            ):

                record.attempts += 1

                if (
                    record.attempts
                    >= settings.otp_max_attempts
                ):
                    record.consumed_at = now

                VerificationRepository.save(
                    db,
                    record,
                )

                db.commit()

                raise HTTPException(
                    status_code=400,
                    detail="Invalid OTP",
                )

          
            record.attempts = 0
            record.consumed_at = now

        
            if purpose == "email_verification":

                user.is_email_verified = True

            elif purpose == "phone_verification":

                user.is_contact_verified = True

            VerificationRepository.save(
                db,
                record,
            )

            db.commit()

            if purpose == "login_2fa":
                return user

            return {
                "message": f"{channel} verification successful"
            }

        except HTTPException:
            raise

        except Exception:

            db.rollback()
            raise
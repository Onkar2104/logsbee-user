from datetime import datetime, timedelta, timezone
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)

from models.login_attempt_model import LoginAttempt
from repositories.user_repository import UserRepository
from repositories.verification_repository import VerificationRepository
from services.verification_service import VerificationService
from core.config import settings


class LoginService:

    @staticmethod
    def _check_login_lock(db: Session, email: str, now: datetime):
        normalized_email = email.strip().lower()
        attempt = db.get(LoginAttempt, normalized_email)
        if attempt is None:
            return
        if attempt.locked_until and attempt.locked_until > now:
            remaining = max(1, int((attempt.locked_until - now).total_seconds()))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many incorrect login attempts. Try again in {remaining} seconds.",
                headers={"Retry-After": str(remaining)},
            )
        if (now - attempt.window_started_at).total_seconds() >= settings.login_attempt_window_seconds:
            attempt.failed_attempts = 0
            attempt.window_started_at = now
            attempt.locked_until = None
            db.commit()

    @staticmethod
    def _record_failed_login(db: Session, email: str, now: datetime):
        normalized_email = email.strip().lower()
        attempt = db.get(LoginAttempt, normalized_email)
        if attempt is None:
            attempt = LoginAttempt(
                email=normalized_email,
                failed_attempts=0,
                window_started_at=now,
            )
            db.add(attempt)
        if (now - attempt.window_started_at).total_seconds() >= settings.login_attempt_window_seconds:
            attempt.failed_attempts = 0
            attempt.window_started_at = now
            attempt.locked_until = None
        attempt.failed_attempts += 1
        if attempt.failed_attempts >= settings.login_max_failed_attempts:
            attempt.locked_until = now + timedelta(minutes=settings.login_lockout_minutes)
        db.commit()
        if attempt.locked_until and attempt.locked_until > now:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Five incorrect login attempts reached. Try again in {settings.login_lockout_minutes} minutes.",
                headers={"Retry-After": str(settings.login_lockout_minutes * 60)},
            )

    @staticmethod
    def _clear_failed_logins(db: Session, email: str):
        attempt = db.get(LoginAttempt, email.strip().lower())
        if attempt is not None:
            db.delete(attempt)
            db.commit()

    @staticmethod
    def _check_account_active(user):
        if user.account_id is not None:
            account = user.account
            if account is None or not account.is_active or account.is_deleted:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="This account is inactive.",
                )

    @staticmethod
    def _check_password_expiry(user):

        if user.password_expires_at is not None:

            expiry = user.password_expires_at

            if expiry.tzinfo is None:
                expiry = expiry.replace(
                    tzinfo=timezone.utc
                )

            if expiry <= datetime.now(timezone.utc):

                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Your password has expired. Please reset your password.",
                )

    @staticmethod
    def _generate_tokens(user):

        return {
            "requires_2fa": False,
            "access_token": create_access_token(
                str(user.id)
            ),
            "refresh_token": create_refresh_token(
                str(user.id)
            ),
            "token_type": "bearer",
        }

    @staticmethod
    def login(
        db: Session,
        email: str,
        password: str,
    ):

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        LoginService._check_login_lock(db, email, now)

        user = UserRepository.get_by_email(
            db,
            email.strip().lower(),
        )

        if (
            not user
            or user.is_deleted
            or not verify_password(
                password,
                user.password_hash if user else "",
            )
        ):
            LoginService._record_failed_login(db, email, now)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        LoginService._clear_failed_logins(db, email)
        LoginService._check_account_active(user)
        LoginService._check_password_expiry(user)

        # Check whether 2FA is enabled.
        if user.is_two_factor_authenticated:

            return VerificationService.send_otp(
                db=db,
                user_id=user.id,
                channel="email",
                purpose="login_2fa",
            )

        # 2FA disabled: Generate tokens immediately.
        return LoginService._generate_tokens(user)

    @staticmethod
    def verify_login_otp(
        db: Session,
        challenge_id: uuid.UUID,
        otp: str,
    ):

        # Retrieve challenge owner from the database.
        record = VerificationRepository.get_by_id(
            db=db,
            challenge_id=challenge_id,
            purpose="login_2fa",
            channel="email",
        )

        if record is None:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired login challenge",
            )

        user = VerificationService.verify_otp(
            db=db,
            user_id=record.user_id,
            channel="email",
            otp=otp,
            purpose="login_2fa",
            challenge_id=challenge_id,
        )

        if (
            user.is_deleted
            or not user.is_two_factor_authenticated
            or not user.is_email_verified
        ):

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Login verification is no longer valid",
            )

        LoginService._check_account_active(user)
        LoginService._check_password_expiry(user)

        return LoginService._generate_tokens(user)

    @staticmethod
    def refresh_access_token(
        db: Session,
        refresh_token: str,
    ):

        payload = decode_token(
            token=refresh_token,
            expected_type="refresh",
        )

        user_id = payload.get("sub")

        # The JWT subject must be a valid UUID before it reaches SQLAlchemy.
        # A malformed subject should be treated as an invalid token, not a 500.
        try:
            user_uuid = uuid.UUID(str(user_id))
        except (ValueError, TypeError, AttributeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = UserRepository.get_by_id(
            db,
            user_uuid,
        )

        if not user or user.is_deleted:

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        LoginService._check_account_active(user)
        LoginService._check_password_expiry(user)

        return {
            "access_token": create_access_token(
                str(user.id)
            ),
            "token_type": "bearer",
        }
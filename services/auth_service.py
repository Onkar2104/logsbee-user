from datetime import datetime, timezone
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)

from repositories.user_repository import UserRepository
from repositories.verification_repository import VerificationRepository
from services.verification_service import VerificationService


class LoginService:

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

        user = UserRepository.get_by_email(
            db,
            email,
        )

        if (
            not user
            or user.is_deleted
            or not verify_password(
                password,
                user.password_hash,
            )
        ):

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

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

        user = UserRepository.get_by_id(
            db,
            user_id,
        )

        if not user or user.is_deleted:

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        LoginService._check_password_expiry(user)

        return {
            "access_token": create_access_token(
                str(user.id)
            ),
            "token_type": "bearer",
        }
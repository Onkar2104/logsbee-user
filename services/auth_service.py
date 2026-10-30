from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from repositories.user_repository import UserRepository


class LoginService:

    @staticmethod
    def login(db: Session, email: str, password: str):
        user = UserRepository.get_by_email(db, email)

        if (
            not user
            or user.is_deleted
            or not verify_password(password, user.password_hash)
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if user.password_expires_at is not None:
            expiry = user.password_expires_at

            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)

            if expiry <= datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Your password has expired. Please reset your password.",
                )

        user_id = str(user.id)

        return {
            "access_token": create_access_token(user_id),
            "refresh_token": create_refresh_token(user_id),
            "token_type": "bearer",
        }
    

    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str):
        payload = decode_token(
            token=refresh_token,
            expected_type="refresh",
        )

        user_id = payload.get("sub")

        user = UserRepository.get_by_id(db, user_id)

        if not user or user.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        if user.password_expires_at is not None:
            expiry = user.password_expires_at

            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)

            if expiry <= datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Password expired. Please reset your password.",
                )

        return {
            "access_token": create_access_token(str(user.id)),
            "token_type": "bearer",
        }
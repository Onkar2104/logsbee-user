from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.security import hash_password
from models.account_model import Account
from models.user_model import User
from repositories.user_repository import UserRepository
from schemas.account_schema import AccountRegistrationCreate
from services.verification_service import VerificationService


class AccountRegistrationService:
    @staticmethod
    def register_account(db: Session, data: AccountRegistrationCreate):
        admin_email = str(data.admin.email).strip().lower()

        if UserRepository.get_by_email(db, admin_email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account already exists with this email address.",
            )

        admin_role = UserRepository.get_by_user_role(db, "admin")
        if admin_role is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="System Admin role is not configured.",
            )

        account = Account(
            name=data.name.strip(),
            email=admin_email,
            contact=data.contact or data.admin.contact,
            address=data.address,
            is_active=False,
            is_registration_pending=True,
            created_by=None,
        )

        try:
            db.add(account)
            db.flush()

            admin = User(
                account_id=account.account_id,
                first_name=data.admin.first_name.strip(),
                last_name=data.admin.last_name.strip(),
                email=admin_email,
                contact=data.admin.contact or data.contact,
                password_hash=hash_password(
                    data.admin.password.get_secret_value()
                ),
                user_role_id=admin_role.id,
                created_by=None,
                is_email_verified=False,
                is_contact_verified=False,
            )
            db.add(admin)
            db.commit()
            db.refresh(account)
            db.refresh(admin)
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account already exists with these details.",
            ) from None
        except Exception:
            db.rollback()
            raise

        email_sent = True
        try:
            VerificationService.send_otp(db, admin.id, "email")
        except HTTPException:
            # Keep the account pending and return its ID so the visitor can
            # request another code without attempting duplicate registration.
            email_sent = False

        return {
            "account_id": account.account_id,
            "admin_user_id": admin.id,
            "email": admin.email,
            "verification_email_sent": email_sent,
            "message": (
                "Registration started. Check your email for the verification code."
                if email_sent
                else "Your registration is saved but the verification email could not be sent. Use Resend code to try again."
            ),
        }

    @staticmethod
    def resend_registration_otp(db: Session, email: str):
        normalized_email = email.strip().lower()
        user = UserRepository.get_by_email(db, normalized_email)

        # Keep the response generic to avoid revealing whether an email is registered.
        if (
            user is None
            or user.account is None
            or not user.account.is_registration_pending
            or user.is_email_verified
            or user.is_deleted
        ):
            return {
                "message": "If a pending registration exists for this email, a verification code has been sent."
            }

        VerificationService.send_otp(db, user.id, "email")
        return {
            "message": "If a pending registration exists for this email, a verification code has been sent."
        }

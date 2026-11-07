from fastapi import HTTPException, status
from sqlalchemy import select
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
        organization_email = data.email.strip().lower()
        admin_email = data.admin.email.strip().lower()

        if UserRepository.get_by_email(db, admin_email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account already exists with the Admin email address.",
            )

        existing_account = db.scalar(
            select(Account).where(
                Account.email == organization_email,
                Account.is_deleted.is_(False),
            )
        )
        if existing_account:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An organization already exists with this email address.",
            )

        admin_role = UserRepository.get_by_user_role(db, "admin")
        if admin_role is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="System Admin role is not configured.",
            )

        account = Account(
            name=data.name.strip(),
            email=organization_email,
            contact=data.contact or data.admin.contact,
            address=data.address,
            is_email_verified=False,
            is_active=False,
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
                password_hash=hash_password(data.admin.password.get_secret_value()),
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
            VerificationService.send_otp(
                db,
                admin.id,
                "email",
                purpose="account_email_verification",
                destination_override=account.email,
            )
        except HTTPException:
            email_sent = False

        return {
            "account_id": account.account_id,
            "admin_user_id": admin.id,
            "email": account.email,
            "verification_email_sent": email_sent,
            "next_step": "account_email",
            "message": (
                "Organization registered. Verify the organization email first."
                if email_sent
                else "Organization registration is saved, but the organization verification email could not be sent. Resend the code to continue."
            ),
        }

    @staticmethod
    def verify_account_email(db: Session, account_id, otp: str):
        account = db.get(Account, account_id)
        if account is None or account.is_deleted:
            raise HTTPException(status_code=404, detail="Organization registration not found")

        admin = db.scalar(
            select(User).where(
                User.account_id == account.account_id,
                User.is_deleted.is_(False),
            ).order_by(User.created_at.asc())
        )
        if admin is None:
            raise HTTPException(status_code=404, detail="Initial Admin account not found")

        result = VerificationService.verify_otp(
            db,
            admin.id,
            "email",
            otp,
            purpose="account_email_verification",
        )

        admin_otp_sent = True
        try:
            VerificationService.send_otp(
                db,
                admin.id,
                "email",
                purpose="email_verification",
            )
        except HTTPException:
            admin_otp_sent = False

        return {
            "account_id": account.account_id,
            "admin_user_id": admin.id,
            "admin_email": admin.email,
            "admin_verification_email_sent": admin_otp_sent,
            "next_step": "admin_email",
            "message": (
                "Organization email verified. Now verify the initial Admin email."
                if admin_otp_sent
                else "Organization email verified, but the Admin verification email could not be sent. Resend the Admin code."
            ),
        }

    @staticmethod
    def resend_registration_otp(db: Session, account_id, verification_type: str):
        account = db.get(Account, account_id)
        generic_message = "If this registration is pending, a verification code has been sent."

        if account is None or account.is_deleted:
            return {"message": generic_message}

        admin = db.scalar(
            select(User).where(
                User.account_id == account.account_id,
                User.is_deleted.is_(False),
            ).order_by(User.created_at.asc())
        )
        if admin is None or account.is_active:
            return {"message": generic_message}

        if verification_type == "account":
            if account.is_email_verified:
                return {"message": "Organization email is already verified."}
            VerificationService.send_otp(
                db,
                admin.id,
                "email",
                purpose="account_email_verification",
                destination_override=account.email,
            )
        elif verification_type == "admin":
            if not account.is_email_verified:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Verify the organization email before requesting Admin email verification.",
                )
            if admin.is_email_verified:
                return {"message": "Admin email is already verified."}
            VerificationService.send_otp(
                db,
                admin.id,
                "email",
                purpose="email_verification",
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid verification type")

        return {"message": generic_message}

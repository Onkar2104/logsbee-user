from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.security import hash_password
from core.user_permissions import check_super_admin
from models.account_model import Account
from models.user_model import User
from repositories.user_repository import UserRepository
from schemas.account_schema import AccountCreate


class AccountService:
    @staticmethod
    def create_account_with_admin(
        db: Session,
        data: AccountCreate,
        current_user,
    ):
        check_super_admin(current_user)

        admin_email = str(data.admin.email).strip().lower()
        if UserRepository.get_by_email(db, admin_email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Admin email already exists.",
            )

        admin_role = UserRepository.get_by_user_role(db, "admin")
        if admin_role is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="System Admin role is not configured.",
            )

        account = Account(
            name=data.name.strip(),
            email=str(data.email).lower() if data.email else None,
            contact=data.contact,
            address=data.address,
            created_by=current_user.id,
        )

        try:
            db.add(account)
            db.flush()

            admin = User(
                account_id=account.account_id,
                first_name=data.admin.first_name.strip(),
                last_name=data.admin.last_name.strip(),
                email=admin_email,
                contact=data.admin.contact,
                password_hash=hash_password(
                    data.admin.password.get_secret_value()
                ),
                user_role_id=admin_role.id,
                created_by=current_user.id,
                is_email_verified=False,
                is_contact_verified=False,
            )
            db.add(admin)
            db.flush()

            result = {
                "account_id": account.account_id,
                "name": account.name,
                "admin_user_id": admin.id,
                "admin_email": admin.email,
                "message": "Account and Admin user created successfully.",
            }
            db.commit()
            return result

        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Account or Admin details conflict with existing data.",
            )
        except Exception:
            db.rollback()
            raise

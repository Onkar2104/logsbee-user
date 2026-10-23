from sqlalchemy.orm import Session

from services.forgot_password_service import ForgotPasswordService


class ForgotPasswordController:

    @staticmethod
    def send_otp(db: Session, email: str):
        return ForgotPasswordService.send_otp(db, email)

    @staticmethod
    def reset_password(
        db: Session,
        email: str,
        otp: str,
        new_password: str,
    ):
        return ForgotPasswordService.reset_password(
            db=db,
            email=email,
            otp=otp,
            new_password=new_password,
        )
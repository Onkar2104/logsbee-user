from sqlalchemy.orm import Session

from schemas.auth_schema import (
    LoginRequest,
    VerifyLoginOTPRequest,
)

from services.auth_service import LoginService


class LoginController:

    @staticmethod
    def login(
        db: Session,
        request: LoginRequest,
    ):

        return LoginService.login(
            db=db,
            email=str(request.email),
            password=request.password.get_secret_value(),
        )


    @staticmethod
    def verify_login_otp(
        db: Session,
        request: VerifyLoginOTPRequest,
    ):

        return LoginService.verify_login_otp(
            db=db,
            challenge_id=request.challenge_id,
            otp=request.otp,
        )


    @staticmethod
    def refresh_token(
        db: Session,
        refresh_token: str,
    ):

        return LoginService.refresh_access_token(
            db=db,
            refresh_token=refresh_token,
        )
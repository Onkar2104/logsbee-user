from sqlalchemy.orm import Session

from schemas.auth_schema import LoginRequest
from services.auth_service import LoginService


class LoginController:

    @staticmethod
    def login(db: Session, request: LoginRequest):
        return LoginService.login(
            db=db,
            email=str(request.email),
            password=request.password.get_secret_value(),
        )

    @staticmethod
    def refresh_token(db: Session, refresh_token: str):
        return LoginService.refresh_access_token(
            db=db,
            refresh_token=refresh_token,
        )
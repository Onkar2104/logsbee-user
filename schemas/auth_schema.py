from uuid import UUID

from pydantic import BaseModel, EmailStr, SecretStr


class LoginRequest(BaseModel):

    email: EmailStr
    password: SecretStr


class LoginResponse(BaseModel):

    requires_2fa: bool = False

    access_token: str | None = None
    refresh_token: str | None = None

    challenge_id: UUID | None = None

    message: str | None = None

    token_type: str = "bearer"


class VerifyLoginOTPRequest(BaseModel):

    challenge_id: UUID
    otp: str


class RefreshTokenRequest(BaseModel):

    refresh_token: str
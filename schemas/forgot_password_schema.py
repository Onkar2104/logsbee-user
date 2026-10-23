from pydantic import BaseModel, EmailStr, Field, SecretStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str = Field(pattern=r"^[0-9]{6}$")
    new_password: SecretStr
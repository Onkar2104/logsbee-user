import uuid
from typing import Optional

from pydantic import BaseModel, Field, SecretStr


class AccountAdminCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=255)
    password: SecretStr = Field(min_length=8, max_length=128)
    contact: Optional[str] = Field(default=None, max_length=20)


class AccountCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: Optional[str] = None
    contact: Optional[str] = Field(default=None, max_length=20)
    address: Optional[str] = None
    admin: AccountAdminCreate


class AccountRegistrationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: str = Field(min_length=3, max_length=255)
    contact: Optional[str] = Field(default=None, max_length=20)
    address: Optional[str] = None
    admin: AccountAdminCreate


class RegistrationResendRequest(BaseModel):
    account_id: uuid.UUID
    verification_type: str = Field(pattern=r"^(account|admin)$")


class AccountEmailVerificationRequest(BaseModel):
    account_id: uuid.UUID
    otp: str = Field(pattern=r"^[0-9]{6}$")


class RegistrationResponse(BaseModel):
    account_id: uuid.UUID
    admin_user_id: uuid.UUID
    email: str
    verification_email_sent: bool
    next_step: str
    message: str


class AccountCreatedResponse(BaseModel):
    account_id: uuid.UUID
    name: str
    admin_user_id: uuid.UUID
    admin_email: str
    message: str

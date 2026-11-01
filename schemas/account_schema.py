import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr


class AccountAdminCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: SecretStr = Field(min_length=8, max_length=128)
    contact: Optional[str] = Field(default=None, max_length=20)


class AccountCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: Optional[EmailStr] = None
    contact: Optional[str] = Field(default=None, max_length=20)
    address: Optional[str] = None
    admin: AccountAdminCreate


class AccountCreatedResponse(BaseModel):
    account_id: uuid.UUID
    name: str
    admin_user_id: uuid.UUID
    admin_email: EmailStr
    message: str

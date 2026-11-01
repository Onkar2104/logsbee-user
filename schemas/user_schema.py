import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class UserCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=255)
    password: SecretStr = Field(min_length=8, max_length=128)
    contact: Optional[str] = Field(default=None, max_length=20)
    country: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = Field(default=None, max_length=20)
    address: Optional[str] = None
    # Optional custom role; omitted means the account's default system User role.
    user_role_id: Optional[uuid.UUID] = None


class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=255)
    contact: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    address: Optional[str] = None
    user_role_id: Optional[uuid.UUID] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: Optional[uuid.UUID]
    first_name: str
    last_name: str
    email: str
    contact: Optional[str]
    country: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    address: Optional[str]
    user_role_id: uuid.UUID
    is_two_factor_authenticated: bool
    is_email_verified: bool
    is_contact_verified: bool
    created_at: datetime
    created_by: Optional[uuid.UUID]
    updated_at: Optional[datetime]
    updated_by: Optional[uuid.UUID]
    is_deleted: bool
    deleted_at: Optional[datetime]
    deleted_by: Optional[uuid.UUID]
    deletion_reason: Optional[str]


class PasswordChange(BaseModel):
    current_password: SecretStr
    new_password: SecretStr = Field(min_length=8, max_length=128)

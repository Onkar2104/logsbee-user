import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class RoleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    description: str | None = None
    permission_codes: list[str] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=50)
    description: str | None = None
    permission_codes: list[str] | None = None


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    code: str
    name: str
    description: str | None


class RoleResponse(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID | None
    name: str
    description: str | None
    is_system_role: bool
    created_at: datetime
    permissions: list[PermissionResponse]

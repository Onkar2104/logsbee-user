import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    code: str = Field(min_length=2, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=2, max_length=120)
    description: str | None = None


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = None
    is_active: bool | None = None


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    code: str
    name: str
    description: str | None
    is_active: bool
    created_at: datetime


class ProductAssignment(BaseModel):
    product_ids: list[uuid.UUID] = Field(default_factory=list)


class AccountProductResponse(BaseModel):
    product_id: uuid.UUID
    code: str
    name: str
    is_enabled: bool
    expires_at: datetime | None


class UserProductResponse(BaseModel):
    product_id: uuid.UUID
    code: str
    name: str
    is_enabled: bool

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class OrganizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    created_at: datetime


class ApiKeyCreateRequest(BaseModel):
    name: str
    environment: str = "production"


class ApiKeyCreateResponse(BaseModel):
    api_key: str
    prefix: str
    id: UUID


class ApiKeyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    environment: str
    prefix: str
    scopes: str
    created_at: datetime
    last_used_at: datetime | None
    revoked: bool
    expires_at: datetime | None

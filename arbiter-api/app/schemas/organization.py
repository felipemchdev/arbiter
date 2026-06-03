from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class OrganizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    created_at: datetime


class ApiKeyCreateResponse(BaseModel):
    api_key: str
    org_id: UUID
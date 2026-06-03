from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    pipeline_id: UUID
    run_id: UUID | None
    type: str
    message: str
    resolved: bool
    created_at: datetime


class AlertResolveResponse(BaseModel):
    resolved: bool = True
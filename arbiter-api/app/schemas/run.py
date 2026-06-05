from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.pipeline import RunStatus

class TaskPayload(BaseModel):
    task_id: str
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    duration_ms: int | None = None
    try_number: int = 1
    log_url: str | None = None
    error_message: str | None = None
    log_output: str | None = None
    input_params: str | None = None

class RunPayload(BaseModel):
    pipeline: str
    source: str = "sdk"
    run_id: str
    status: RunStatus
    started_at: datetime
    finished_at: datetime | None = None
    duration_ms: int | None = None
    error_message: str | None = None
    dag_id: str | None = None
    nodes: list[dict] = Field(default_factory=list)
    edges: list[dict] = Field(default_factory=list)
    tasks: list[TaskPayload] = Field(default_factory=list)

class RunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    pipeline_id: UUKD
    run_id: str
    status: RunStatus
    started_at: datetime
    finished_at: datetime | None
    duration_ms: int | None
    error_message: str | None
    created_at: datetime

class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    run_id: UUID
    task_id: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    duration_ms: int | None
    try_number: int
    log_url: str | None
    error_message: str | None
    log_output: str | None
    input_params: str | None
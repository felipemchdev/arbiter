from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.pipeline import PipelineSource, RunStatus


class PipelineCreate(BaseModel):
    name: str
    source: PipelineSource
    dag_id: str | None = None


class DagDefinitionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nodes: list[dict] = Field(default_factory=list)
    edges: list[dict] = Field(default_factory=list)
    updated_at: datetime


class PipelineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    source: PipelineSource
    dag_id: str | None
    last_run_status: RunStatus | None
    last_run_at: datetime | None
    created_at: datetime


class PipelineDetail(PipelineRead):
    dag_definition: DagDefinitionRead | None = None


class PipelineRunSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    run_id: str
    status: RunStatus
    started_at: datetime
    finished_at: datetime | None
    duration_ms: int | None
    error_message: str | None
    created_at: datetime
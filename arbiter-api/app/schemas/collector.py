from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.run import TaskPayload


class AirflowRunSnapshot(BaseModel):
    run_id: str
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    duration_ms: int | None = None
    error_message: str | None = None
    tasks: list[TaskPayload] = Field(default_factory=list)


class AirflowDagSnapshot(BaseModel):
    dag_id: str
    name: str
    nodes: list[dict] = Field(default_factory=list)
    edges: list[dict] = Field(default_factory=list)
    runs: list[AirflowRunSnapshot] = Field(default_factory=list)


class AirflowSyncPayload(BaseModel):
    dags: list[AirflowDagSnapshot] = Field(default_factory=list)
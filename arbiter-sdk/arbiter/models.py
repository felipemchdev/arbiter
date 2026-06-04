from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class TaskPayload(BaseModel):
    task_id: str
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    duration_ms: int | None = None
    try_number: int = 1
    log_url: str | None = None
    error_message: str | None = None


class RunPayload(BaseModel):
    pipeline: str
    source: str = "sdk"
    run_id: str = Field(default_factory=lambda: "")
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    duration_ms: int | None = None
    error_message: str | None = None
    dag_id: str | None = None
    nodes: list[dict[str, Any]] = Field(default_factory=list)
    edges: list[dict[str, Any]] = Field(default_factory=list)
    tasks: list[TaskPayload] = Field(default_factory=list)
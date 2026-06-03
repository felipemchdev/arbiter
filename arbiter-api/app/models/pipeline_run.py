from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.pipeline import RunStatus


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    pipeline_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pipelines.id"), nullable=False, index=True)
    run_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[RunStatus] = mapped_column(Enum(RunStatus, name="runstatus"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    pipeline: Mapped["Pipeline"] = relationship(back_populates="runs")
    task_instances: Mapped[list["TaskInstance"]] = relationship(back_populates="run", cascade="all, delete-orphan")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="run")
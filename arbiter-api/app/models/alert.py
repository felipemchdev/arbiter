from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AlertType(str, enum.Enum):
    failure = "failure"
    duration_exceeded = "duration_exceeded"
    no_run = "no_run"


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    pipeline_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pipelines.id"), nullable=False, index=True)
    run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("pipeline_runs.id"), nullable=True)
    type: Mapped[AlertType] = mapped_column(Enum(AlertType, name="alerttype"), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    pipeline: Mapped["Pipeline"] = relationship(back_populates="alerts")
    run: Mapped["PipelineRun | None"] = relationship(back_populates="alerts")
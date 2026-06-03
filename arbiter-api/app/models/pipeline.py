from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PipelineSource(str, enum.Enum):
    airflow = "airflow"
    azure_function = "azure_function"
    sdk = "sdk"


class RunStatus(str, enum.Enum):
    running = "running"
    success = "success"
    failed = "failed"
    skipped = "skipped"


class Pipeline(Base):
    __tablename__ = "pipelines"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[PipelineSource] = mapped_column(Enum(PipelineSource, name="pipelinesource"), nullable=False)
    dag_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_run_status: Mapped[RunStatus | None] = mapped_column(Enum(RunStatus, name="runstatus"), nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    organization: Mapped["Organization"] = relationship(back_populates="pipelines")
    runs: Mapped[list["PipelineRun"]] = relationship(back_populates="pipeline", cascade="all, delete-orphan")
    dag_definition: Mapped["DagDefinition | None"] = relationship(back_populates="pipeline", cascade="all, delete-orphan", uselist=False)
    alerts: Mapped[list["Alert"]] = relationship(back_populates="pipeline", cascade="all, delete-orphan")
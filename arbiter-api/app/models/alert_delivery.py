from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AlertDeliveryStatus(str, enum.Enum):
    pending = "pending"
    delivered = "delivered"
    failed = "failed"


class AlertDelivery(Base):
    """One outbox row: the attempt to push one alert to one channel."""

    __tablename__ = "alert_deliveries"
    __table_args__ = (
        UniqueConstraint("alert_id", "channel_id", name="uq_alert_delivery_channel"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    alert_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("alerts.id"), nullable=False, index=True)
    channel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("notification_channels.id"), nullable=False, index=True
    )
    status: Mapped[AlertDeliveryStatus] = mapped_column(
        Enum(AlertDeliveryStatus, name="altdeliverystatus"),
        nullable=False,
        default=AlertDeliveryStatus.pending,
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    response_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    last_error: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
    next_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    is_test: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    alert: Mapped["Alert"] = relationship()
    channel: Mapped["NotificationChannel"] = relationship(back_populates="deliveries")

from datetime import datetime
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _checked_url(v: str) -> str:
    """Accept only a plain absolute HTTP or HTTPS endpoint."""
    parts = urlsplit(v)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise ValueError("url must be an absolute http or https endpoint")
    if " " in v:
        raise ValueError("url must not contain spaces")
    return v


class NotificationChannelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    url: str = Field(min_length=8, max_length=2048)
    enabled: bool = True

    @field_validator("url")
    @classmethod
    def _check_url(cls, v: str) -> str:
        return _checked_url(v)


class NotificationChannelUpdate(BaseModel):
    """Partial change of one channel; an omitted field keeps its current value."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    url: str | None = Field(default=None, min_length=8, max_length=2048)
    enabled: bool | None = None

    @field_validator("url")
    @classmethod
    def _check_url(cls, v: str | None) -> str | None:
        return v if v is None else _checked_url(v)


class AlertDeliveryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    alert_id: UUID
    channel_id: UUID
    status: str
    attempts: int
    response_status_code: int | None
    last_error: str | None
    next_attempt_at: datetime | None
    delivered_at: datetime | None
    created_at: datetime


class NotificationChannelRead(BaseModel):
    """A channel without its signing secret, which the API returns only once."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    url: str
    enabled: bool
    created_at: datetime
    last_delivery: AlertDeliveryRead | None = None


class NotificationChannelCreateResponse(NotificationChannelRead):
    signing_secret: str


class TestSendResponse(BaseModel):
    delivered: bool
    status_code: int | None
    error: str | None

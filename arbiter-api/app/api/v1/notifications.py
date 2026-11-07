from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_org, get_db
from app.api.role_guard import require_owner
from app.models.alert_delivery import AlertDeliveryStatus
from app.schemas.notification import (
    AlertDeliveryRead,
    NotificationChannelCreate,
    NotificationChannelCreateResponse,
    NotificationChannelRead,
    NotificationChannelUpdate,
    TestSendResponse,
)
from app.schemas.page import Page
from app.services import notification_service

router = APIRouter()


def _read_channel(channel, last_delivery) -> NotificationChannelRead:
    """One channel with its most recent delivery, as the dashboard reads it."""
    return NotificationChannelRead(
        id=channel.id,
        name=channel.name,
        url=channel.url,
        enabled=channel.enabled,
        created_at=channel.created_at,
        last_delivery=(
            None if last_delivery is None else AlertDeliveryRead.model_validate(last_delivery)
        ),
    )


@router.get("", response_model=list[NotificationChannelRead])
async def read_channels(
    current_org=Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """List the alert webhook channels of the organisation, newest first."""
    pairs = await notification_service.list_channels(db, current_org.id)
    return [_read_channel(channel, last) for channel, last in pairs]


@router.get("/deliveries", response_model=Page[AlertDeliveryRead])
async def read_deliveries(
    current_org=Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
    delivery_status: AlertDeliveryStatus | None = Query(default=None, alias="status"),
    channel_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """List delivery attempts of the organisation, newest first."""
    items, total = await notification_service.list_deliveries(
        db,
        current_org.id,
        delivery_status=delivery_status,
        channel_id=channel_id,
        limit=limit,
        offset=offset,
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=NotificationChannelCreateResponse)
async def create_channel_endpoint(
    body: NotificationChannelCreate,
    current_org=Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """Register a channel. The response shows the signing secret one time only."""
    try:
        channel, secret = await notification_service.create_channel(
            db, current_org.id, name=body.name, url=body.url, enabled=body.enabled
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return NotificationChannelCreateResponse(
        id=channel.id,
        name=channel.name,
        url=channel.url,
        enabled=channel.enabled,
        created_at=channel.created_at,
        signing_secret=secret,
    )


async def _owned_channel(channel_id: UUID, org_id, db: AsyncSession):
    """Load a channel of this organisation, or answer 404 for one that is not there."""
    channel = await notification_service.get_channel(db, channel_id, org_id)
    if channel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="channel not found")
    return channel


@router.patch("/{channel_id}", response_model=NotificationChannelRead)
async def update_channel_endpoint(
    channel_id: UUID,
    body: NotificationChannelUpdate,
    current_org=Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """Change the name, the endpoint or the enabled flag of one channel."""
    channel = await _owned_channel(channel_id, current_org.id, db)
    channel = await notification_service.update_channel(
        db,
        channel,
        name=body.name,
        url=body.url,
        enabled=body.enabled,
        changed=body.model_fields_set,
    )
    last = await notification_service.last_delivery_for(db, channel.id)
    return _read_channel(channel, last)


@router.post("/{channel_id}/test", response_model=TestSendResponse)
async def test_channel_endpoint(
    channel_id: UUID,
    current_org=Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """Send one sample payload now and report what the endpoint answered."""
    channel = await _owned_channel(channel_id, current_org.id, db)
    return TestSendResponse(**await notification_service.test_channel_send(db, channel))


@router.delete("/{channel_id}")
async def delete_channel_endpoint(
    channel_id: UUID,
    current_org=Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """Remove a channel and every delivery still queued for it."""
    channel = await _owned_channel(channel_id, current_org.id, db)
    await notification_service.delete_channel(db, channel)
    return {"detail": "notification channel deleted"}

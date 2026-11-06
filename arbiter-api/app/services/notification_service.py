from __future__ import annotations

import hashlib
import hmac
import json
import logging
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import httpx
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.alert import Alert
from app.models.alert_delivery import AlertDelivery, AlertDeliveryStatus
from app.models.notification_channel import NotificationChannel
from app.models.pipeline import Pipeline
from app.models.pipeline_run import PipelineRun

logger = logging.getLogger(__name__)

SIGNATURE_HEADER = "X-Arbiter-Signature"
DELIVERY_HEADER = "X-Arbiter-Delivery"
ATTEMPT_HEADER = "X-Arbiter-Attempt"
USER_AGENT = "arbiter-webhook/0.1"
SECRET_PREFIX = "arbwhk_"
MAX_CHANNELS_PER_ORG = 10
MAX_ERROR_LENGTH = 500
# A lease, not a timeout: a worker that dies mid-send leaves the row pending again.
CLAIM_LEASE_SECONDS = 300
# Bound to httpx.AsyncClient. The tests swap this name for a fake client, because the
# shared httpx.AsyncClient must stay intact: the API test client uses it too.
async_client_factory = httpx.AsyncClient


def generate_signing_secret() -> str:
    return SECRET_PREFIX + secrets.token_hex(24)


def canonical_json(payload: dict) -> bytes:
    """The exact bytes that are signed and sent, so a receiver can recompute the HMAC."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_body(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


async def send_webhook(
    channel: NotificationChannel,
    payload: dict,
    *,
    delivery_id,
    attempt: int,
) -> tuple[int | None, str | None, bool]:
    """POST one payload. Return (response status code, error text, delivered)."""
    body = canonical_json(payload)
    headers = {
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
        SIGNATURE_HEADER: sign_body(channel.signing_secret, body),
        DELIVERY_HEADER: str(delivery_id),
        ATTEMPT_HEADER: str(attempt),
    }
    try:
        async with async_client_factory(timeout=settings.notification_timeout_seconds) as client:
            response = await client.post(channel.url, content=body, headers=headers)
    except httpx.HTTPError as exc:
        return None, f"{type(exc).__name__}: {exc}"[:MAX_ERROR_LENGTH], False
    except Exception as exc:  # noqa: BLE001
        logger.exception("webhook_send_crashed channel_id=%s", channel.id)
        return None, f"{type(exc).__name__}: {exc}"[:MAX_ERROR_LENGTH], False

    if 200 <= response.status_code < 300:
        return response.status_code, None, True
    return response.status_code, f"endpoint replied {response.status_code}"[:MAX_ERROR_LENGTH], False


def _iso(value) -> str | None:
    return value.isoformat() if value is not None else None


def build_alert_payload(
    *,
    alert: Alert,
    pipeline: Pipeline,
    run: PipelineRun | None,
    delivery_id,
    attempt: int,
) -> dict:
    """The webhook body: the alert, its pipeline and, when known, its run."""
    return {
        "delivery_id": str(delivery_id),
        "attempt": attempt,
        "sent_at": _iso(datetime.now(UTC)),
        "alert": {
            "id": str(alert.id),
            "type": alert.type.value,
            "message": alert.message,
            "resolved": alert.resolved,
            "created_at": _iso(alert.created_at),
        },
        "pipeline": {"id": str(pipeline.id), "name": pipeline.name},
        "run": None
        if run is None
        else {
            "id": str(run.id),
            "run_id": run.run_id,
            "status": run.status.value,
            "started_at": _iso(run.started_at),
            "finished_at": _iso(run.finished_at),
            "duration_ms": run.duration_ms,
            "error_message": run.error_message,
        },
    }


async def queue_alert_deliveries(session: AsyncSession, alert: Alert) -> int:
    """Write one pending outbox row per enabled channel, inside the caller's transaction.

    The rows share the alert transaction: an alert that is stored is an alert that
    will be sent, and an alert that rolls back leaves no delivery behind.
    """
    if not settings.notifications_enabled:
        return 0
    org_id_result = await session.execute(
        select(Pipeline.org_id).where(Pipeline.id == alert.pipeline_id)
    )
    org_id = org_id_result.scalar_one_or_none()
    if org_id is None:
        return 0
    channels = (
        await session.execute(
            select(NotificationChannel).where(
                NotificationChannel.org_id == org_id,
                NotificationChannel.enabled == True,  # noqa: E712
            )
        )
    ).scalars().all()

    queued = 0
    for channel in channels:
        delivery = AlertDelivery(alert_id=alert.id, channel_id=channel.id)
        try:
            # The savepoint keeps a duplicate (alert, channel) pair from poisoning
            # the ingest transaction when two events race.
            async with session.begin_nested():
                session.add(delivery)
                await session.flush()
            queued += 1
        except IntegrityError:
            if delivery in session:
                session.expunge(delivery)
    if queued:
        logger.info("alert_deliveries_queued", extra={"alert_id": str(alert.id), "count": queued})
    return queued


async def deliver_due_alerts(session: AsyncSession, *, org_id=None, limit: int = 50) -> dict[str, int]:
    """Send every due delivery once. Return the counts per outcome.

    Pass ``org_id`` to work on one organisation's queue; the periodic worker
    leaves it out and drains every queue.
    """
    now = datetime.now(UTC)
    statement = (
        select(AlertDelivery.id, AlertDelivery.attempts)
        .join(Alert, Alert.id == AlertDelivery.alert_id)
        .where(
            AlertDelivery.status == AlertDeliveryStatus.pending,
            (AlertDelivery.next_attempt_at.is_(None))
            | (AlertDelivery.next_attempt_at <= now),
        )
        .order_by(AlertDelivery.created_at)
        .limit(limit)
    )
    if org_id is not None:
        statement = statement.join(Pipeline, Pipeline.id == Alert.pipeline_id).where(
            Pipeline.org_id == org_id
        )
    due = (await session.execute(statement)).all()

    counts = {"delivered": 0, "retry": 0, "failed": 0, "skipped": 0}
    for delivery_id, attempts in due:
        outcome = await _deliver_one(session, delivery_id, attempts, now)
        counts[outcome] += 1
    return counts


async def _deliver_one(
    session: AsyncSession, delivery_id: UUID, expected_attempts: int, now: datetime
) -> str:
    """Claim one row, send it, store the result. Returns delivered/retry/failed/skipped."""
    claim = await session.execute(
        update(AlertDelivery)
        .where(
            AlertDelivery.id == delivery_id,
            AlertDelivery.status == AlertDeliveryStatus.pending,
            AlertDelivery.attempts == expected_attempts,
        )
        .values(
            attempts=expected_attempts + 1,
            next_attempt_at=now + timedelta(seconds=CLAIM_LEASE_SECONDS),
        )
    )
    if claim.rowcount != 1:
        await session.rollback()
        return "skipped"

    delivery = await session.get(AlertDelivery, delivery_id)
    if delivery is None:
        await session.rollback()
        return "skipped"
    channel = await session.get(NotificationChannel, delivery.channel_id)
    alert = await session.get(Alert, delivery.alert_id)
    if channel is None or alert is None or not channel.enabled:
        delivery.status = AlertDeliveryStatus.failed
        delivery.last_error = "channel removed or disabled"
        await session.commit()
        return "failed"

    pipeline = await session.get(Pipeline, alert.pipeline_id)
    run = None if alert.run_id is None else await session.get(PipelineRun, alert.run_id)
    if pipeline is None:
        delivery.status = AlertDeliveryStatus.failed
        delivery.last_error = "pipeline removed"
        await session.commit()
        return "failed"

    payload = build_alert_payload(
        alert=alert,
        pipeline=pipeline,
        run=run,
        delivery_id=delivery.id,
        attempt=delivery.attempts,
    )
    status_code, error, delivered = await send_webhook(
        channel, payload, delivery_id=delivery.id, attempt=delivery.attempts
    )
    delivery.response_status_code = status_code
    delivery.last_error = error

    if delivered:
        delivery.status = AlertDeliveryStatus.delivered
        delivery.delivered_at = datetime.now(UTC)
        delivery.next_attempt_at = None
        await session.commit()
        logger.info(
            "alert_delivered",
            extra={"delivery_id": str(delivery.id), "channel_id": str(channel.id)},
        )
        return "delivered"

    if delivery.attempts >= settings.notification_max_attempts:
        delivery.status = AlertDeliveryStatus.failed
        delivery.next_attempt_at = None
        await session.commit()
        logger.warning(
            "alert_delivery_exhausted delivery_id=%s attempts=%s",
            delivery.id,
            delivery.attempts,
        )
        return "failed"

    backoff = settings.notification_backoff_seconds * 2 ** (delivery.attempts - 1)
    delivery.next_attempt_at = datetime.now(UTC) + timedelta(seconds=backoff)
    await session.commit()
    return "retry"


async def list_channels(session: AsyncSession, org_id) -> list[tuple[NotificationChannel, AlertDelivery | None]]:
    """Every channel of the organisation with its most recent delivery."""
    channels = (
        await session.execute(
            select(NotificationChannel)
            .where(NotificationChannel.org_id == org_id)
            .order_by(NotificationChannel.created_at.desc())
        )
    ).scalars().all()
    pairs: list[tuple[NotificationChannel, AlertDelivery | None]] = []
    for channel in channels:
        last = (
            await session.execute(
                select(AlertDelivery)
                .where(AlertDelivery.channel_id == channel.id)
                .order_by(AlertDelivery.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        pairs.append((channel, last))
    return pairs


async def update_channel(
    session: AsyncSession,
    channel: NotificationChannel,
    *,
    name: str | None,
    url: str | None,
    enabled: bool | None,
    changed: set[str],
) -> NotificationChannel:
    """Apply only the fields present in the payload."""
    if "name" in changed and name is not None:
        channel.name = name
    if "url" in changed and url is not None:
        channel.url = url
    if "enabled" in changed and enabled is not None:
        channel.enabled = enabled
    session.add(channel)
    await session.commit()
    await session.refresh(channel)
    return channel


async def last_delivery_for(session: AsyncSession, channel_id) -> AlertDelivery | None:
    return (
        await session.execute(
            select(AlertDelivery)
            .where(AlertDelivery.channel_id == channel_id)
            .order_by(AlertDelivery.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()


async def list_deliveries(
    session: AsyncSession,
    org_id,
    *,
    delivery_status: AlertDeliveryStatus | None = None,
    channel_id: UUID | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[AlertDelivery], int]:
    """Page through the delivery attempts of one organisation, newest first."""
    conditions = [Pipeline.org_id == org_id]
    if delivery_status is not None:
        conditions.append(AlertDelivery.status == delivery_status)
    if channel_id is not None:
        conditions.append(AlertDelivery.channel_id == channel_id)

    base = (
        select(AlertDelivery)
        .join(Alert, Alert.id == AlertDelivery.alert_id)
        .join(Pipeline, Pipeline.id == Alert.pipeline_id)
        .where(*conditions)
    )
    total_result = await session.execute(
        select(func.count())
        .select_from(AlertDelivery)
        .join(Alert, Alert.id == AlertDelivery.alert_id)
        .join(Pipeline, Pipeline.id == Alert.pipeline_id)
        .where(*conditions)
    )
    result = await session.execute(
        base.order_by(AlertDelivery.created_at.desc()).limit(limit).offset(offset)
    )
    return list(result.scalars().all()), total_result.scalar_one()


async def create_channel(
    session: AsyncSession,
    org_id,
    *,
    name: str,
    url: str,
    enabled: bool = True,
) -> tuple[NotificationChannel, str]:
    """Store a channel and return it with its one-time signing secret."""
    existing = await session.execute(
        select(NotificationChannel).where(NotificationChannel.org_id == org_id)
    )
    if len(existing.scalars().all()) >= MAX_CHANNELS_PER_ORG:
        raise ValueError(f"an organisation can register at most {MAX_CHANNELS_PER_ORG} channels")

    secret = generate_signing_secret()
    channel = NotificationChannel(
        org_id=org_id, name=name, url=url, signing_secret=secret, enabled=enabled
    )
    session.add(channel)
    await session.commit()
    await session.refresh(channel)
    logger.info("notification_channel_created", extra={"channel_id": str(channel.id)})
    return channel, secret


async def get_channel(session: AsyncSession, channel_id, org_id) -> NotificationChannel | None:
    try:
        parsed = UUID(str(channel_id))
    except (ValueError, TypeError):
        return None
    result = await session.execute(
        select(NotificationChannel).where(
            NotificationChannel.id == parsed, NotificationChannel.org_id == org_id
        )
    )
    return result.scalar_one_or_none()


async def delete_channel(session: AsyncSession, channel: NotificationChannel) -> None:
    """Drop the channel and its queue, so no row keeps an FK to it."""
    pending = await session.execute(
        select(AlertDelivery).where(AlertDelivery.channel_id == channel.id)
    )
    for delivery in pending.scalars().all():
        await session.delete(delivery)
    await session.delete(channel)
    await session.commit()
    logger.info("notification_channel_deleted", extra={"channel_id": str(channel.id)})


async def test_channel_send(session: AsyncSession, channel: NotificationChannel) -> dict:
    """Send one sample payload now and report what the endpoint answered."""
    now = datetime.now(UTC)
    payload = {
        "delivery_id": "test",
        "attempt": 1,
        "sent_at": now.isoformat(),
        "alert": {
            "id": "test",
            "type": "failure",
            "message": "Arbiter test notification for channel " + channel.name,
            "resolved": False,
            "created_at": now.isoformat(),
        },
        "pipeline": {"id": "test", "name": "test"},
        "run": None,
    }
    status_code, error, delivered = await send_webhook(
        channel, payload, delivery_id="test", attempt=1
    )
    return {
        "delivered": delivered,
        "status_code": status_code,
        "error": error,
    }

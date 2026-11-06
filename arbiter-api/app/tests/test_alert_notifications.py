from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings
from app.core.database import Base
from app.core.security import hash_password
from app.models.alert import Alert, AlertType
from app.models.alert_delivery import AlertDelivery, AlertDeliveryStatus
from app.models.notification_channel import NotificationChannel
from app.models.organization import Organization
from app.models.pipeline import Pipeline, PipelineSource
from app.models.user import User
from app.services import notification_service, pipeline_service

pytestmark = pytest.mark.asyncio

CHANNELS_URL = "/api/v1/notification-channels"


class FakeEndpoint:
    """Stand-in for the receiver: records each POST and answers with a fixed result."""

    def __init__(self, status_code: int | None = 200) -> None:
        self.status_code = status_code
        self.calls: list[dict] = []

    def __call__(self, *args, **kwargs) -> "FakeEndpoint":
        return self

    async def __aenter__(self) -> "FakeEndpoint":
        return self

    async def __aexit__(self, *exc) -> bool:
        return False

    async def post(self, url, content=None, headers=None) -> httpx.Response:
        self.calls.append({"url": url, "content": content, "headers": headers})
        request = httpx.Request("POST", url)
        if self.status_code is None:
            raise httpx.ConnectError("connection refused", request=request)
        return httpx.Response(self.status_code, request=request)


async def create_channel(
    client, headers, *, name="ops", url="https://hook.example.test/arbiter", **extra
):
    response = await client.post(
        CHANNELS_URL, headers=headers, json={"name": name, "url": url, **extra}
    )
    assert response.status_code == 200, response.text
    return response.json()


async def send_failed_run(client, headers, *, pipeline: str, run_id: str):
    response = await client.post(
        "/api/v1/runs",
        headers=headers,
        json={
            "pipeline": pipeline,
            "source": "sdk",
            "run_id": run_id,
            "status": "failed",
            "started_at": datetime(2026, 11, 1, 12, 0, tzinfo=UTC).isoformat(),
            "finished_at": datetime(2026, 11, 1, 12, 5, tzinfo=UTC).isoformat(),
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


async def queue_of(session, organization) -> list[AlertDelivery]:
    """The delivery rows of one organisation, oldest first."""
    rows = await session.execute(
        select(AlertDelivery, Pipeline.org_id)
        .join(Alert, Alert.id == AlertDelivery.alert_id)
        .join(Pipeline, Pipeline.id == Alert.pipeline_id)
        .where(Pipeline.org_id == organization.id)
        .order_by(AlertDelivery.created_at)
    )
    return [row for row, _ in rows.all()]


async def test_create_channel_returns_the_secret_once_and_never_again(client, auth_headers):
    created = await create_channel(client, auth_headers, name="ops-room")

    assert created["signing_secret"].startswith("arbwhk_")
    assert len(created["signing_secret"]) > 32

    listed = await client.get(CHANNELS_URL, headers=auth_headers)
    assert listed.status_code == 200
    row = next(item for item in listed.json() if item["name"] == "ops-room")
    assert "signing_secret" not in row
    assert row["url"] == "https://hook.example.test/arbiter"
    assert row["enabled"] is True


async def test_create_channel_rejects_a_non_http_url(client, auth_headers):
    for bad in ["ftp://hook.example.test/x", "hook.example.test/x", "https://"]:
        response = await client.post(
            CHANNELS_URL, headers=auth_headers, json={"name": "bad", "url": bad}
        )
        assert response.status_code == 422, bad
        entry = response.json()["detail"][0]
        assert entry["loc"] == ["body", "url"]
        assert "http" in entry["msg"]


async def test_viewer_reads_but_never_writes_channels(
    client, session, organization, auth_headers
):
    viewer = User(
        id=uuid.uuid4(),
        email=f"viewer+{uuid.uuid4().hex[:8]}@test.local",
        hashed_password=hash_password("testpass123"),
        role="viewer",
        org_id=organization.id,
    )
    session.add(viewer)
    await session.commit()
    token = await client.post(
        "/api/v1/auth/token", data={"username": viewer.email, "password": "testpass123"}
    )
    viewer_headers = {"Authorization": f"Bearer {token.json()['access_token']}"}

    created = await create_channel(client, auth_headers)

    refused = await client.post(
        CHANNELS_URL, headers=viewer_headers, json={"name": "v", "url": "https://a.test/h"}
    )
    assert refused.status_code == 403
    assert (
        await client.delete(f"{CHANNELS_URL}/{created['id']}", headers=viewer_headers)
    ).status_code == 403
    assert (await client.get(CHANNELS_URL, headers=viewer_headers)).status_code == 200


async def test_failure_alert_queues_one_delivery_per_enabled_channel(
    client, session, organization, auth_headers
):
    await create_channel(client, auth_headers, name="primary")
    await create_channel(
        client, auth_headers, name="muted", url="https://muted.test/h", enabled=False
    )

    await send_failed_run(client, auth_headers, pipeline="queued_etl", run_id="queued-1")

    rows = await queue_of(session, organization)
    assert len(rows) == 1
    assert rows[0].status == AlertDeliveryStatus.pending
    assert rows[0].attempts == 0
    alert = await session.get(Alert, rows[0].alert_id)
    assert alert.type.value == "failure"


async def test_duplicate_alert_does_not_queue_a_second_delivery(
    client, session, organization, auth_headers
):
    await create_channel(client, auth_headers)
    await send_failed_run(client, auth_headers, pipeline="dup_etl", run_id="dup-1")
    await send_failed_run(client, auth_headers, pipeline="dup_etl", run_id="dup-1")

    assert len(await queue_of(session, organization)) == 1


async def test_worker_posts_a_signed_payload_and_marks_the_delivery_delivered(
    client, session, organization, auth_headers, monkeypatch
):
    endpoint = FakeEndpoint(200)
    monkeypatch.setattr(notification_service, "async_client_factory", endpoint)
    created = await create_channel(client, auth_headers, name="signed")
    await send_failed_run(client, auth_headers, pipeline="signed_etl", run_id="signed-1")
    queued = (await queue_of(session, organization))[0]

    counts = await notification_service.deliver_due_alerts(session, org_id=organization.id)

    assert counts == {"delivered": 1, "retry": 0, "failed": 0, "skipped": 0}
    assert len(endpoint.calls) == 1
    call = endpoint.calls[0]
    assert call["url"] == "https://hook.example.test/arbiter"
    expected = "sha256=" + hmac.new(
        created["signing_secret"].encode(), call["content"], hashlib.sha256
    ).hexdigest()
    assert call["headers"]["X-Arbiter-Signature"] == expected
    assert call["headers"]["X-Arbiter-Delivery"] == str(queued.id)
    assert call["headers"]["Content-Type"] == "application/json"

    payload = json.loads(call["content"])
    assert payload["alert"]["type"] == "failure"
    assert payload["alert"]["message"]
    assert payload["pipeline"]["name"] == "signed_etl"
    assert payload["run"]["run_id"] == "signed-1"
    assert payload["attempt"] == 1

    row = await session.get(AlertDelivery, queued.id)
    assert row.status == AlertDeliveryStatus.delivered
    assert row.response_status_code == 200
    assert row.delivered_at is not None
    assert row.last_error is None


async def test_channel_list_carries_the_last_delivery(
    client, session, organization, auth_headers, monkeypatch
):
    endpoint = FakeEndpoint(200)
    monkeypatch.setattr(notification_service, "async_client_factory", endpoint)
    await create_channel(client, auth_headers, name="summary")
    await send_failed_run(client, auth_headers, pipeline="summary_etl", run_id="summary-1")
    await notification_service.deliver_due_alerts(session, org_id=organization.id)

    listed = await client.get(CHANNELS_URL, headers=auth_headers)
    row = next(item for item in listed.json() if item["name"] == "summary")
    assert row["last_delivery"]["status"] == "delivered"
    assert row["last_delivery"]["response_status_code"] == 200


async def test_server_error_is_retried_and_exhaustion_marks_it_failed(
    client, session, organization, auth_headers, monkeypatch
):
    monkeypatch.setattr(settings, "notification_max_attempts", 2)
    monkeypatch.setattr(settings, "notification_backoff_seconds", 0)
    endpoint = FakeEndpoint(500)
    monkeypatch.setattr(notification_service, "async_client_factory", endpoint)
    await create_channel(client, auth_headers, name="flaky", url="https://flaky.test/h")
    await send_failed_run(client, auth_headers, pipeline="flaky_etl", run_id="flaky-1")

    first = await notification_service.deliver_due_alerts(session, org_id=organization.id)
    assert first == {"delivered": 0, "retry": 1, "failed": 0, "skipped": 0}
    row = (await queue_of(session, organization))[0]
    assert row.status == AlertDeliveryStatus.pending
    assert row.attempts == 1
    assert row.response_status_code == 500
    assert "500" in row.last_error

    second = await notification_service.deliver_due_alerts(session, org_id=organization.id)
    assert second["failed"] == 1
    row = await session.get(AlertDelivery, row.id)
    assert row.status == AlertDeliveryStatus.failed
    assert row.attempts == 2
    assert row.next_attempt_at is None
    assert len(endpoint.calls) == 2


async def test_connection_error_is_reported_and_retried(
    client, session, organization, auth_headers, monkeypatch
):
    endpoint = FakeEndpoint(None)
    monkeypatch.setattr(notification_service, "async_client_factory", endpoint)
    await create_channel(client, auth_headers, name="down", url="https://down.test/h")
    await send_failed_run(client, auth_headers, pipeline="down_etl", run_id="down-1")

    counts = await notification_service.deliver_due_alerts(session, org_id=organization.id)

    assert counts["retry"] == 1
    row = (await queue_of(session, organization))[0]
    assert "ConnectError" in row.last_error


async def test_a_delivery_inside_its_lease_is_not_sent_twice(
    client, session, organization, auth_headers, monkeypatch
):
    endpoint = FakeEndpoint(200)
    monkeypatch.setattr(notification_service, "async_client_factory", endpoint)
    await create_channel(client, auth_headers, name="leased", url="https://leased.test/h")
    await send_failed_run(client, auth_headers, pipeline="leased_etl", run_id="leased-1")
    await notification_service.deliver_due_alerts(session, org_id=organization.id)

    row = (await queue_of(session, organization))[0]
    row.status = AlertDeliveryStatus.pending
    row.next_attempt_at = datetime.now(UTC) + timedelta(seconds=120)
    await session.commit()

    counts = await notification_service.deliver_due_alerts(session, org_id=organization.id)

    assert counts == {"delivered": 0, "retry": 0, "failed": 0, "skipped": 0}
    assert len(endpoint.calls) == 1


async def test_delete_channel_drops_its_queued_deliveries(
    client, session, organization, auth_headers
):
    created = await create_channel(client, auth_headers, name="doomed")
    await send_failed_run(client, auth_headers, pipeline="doomed_etl", run_id="doomed-1")
    assert len(await queue_of(session, organization)) == 1

    response = await client.delete(f"{CHANNELS_URL}/{created['id']}", headers=auth_headers)

    assert response.status_code == 200
    assert await queue_of(session, organization) == []


async def test_deleting_a_pipeline_removes_its_alert_deliveries():
    engine = create_async_engine("sqlite+aiosqlite://")
    try:
        async with engine.connect() as connection:
            await connection.exec_driver_sql("PRAGMA foreign_keys=ON")
            await connection.run_sync(Base.metadata.create_all)
            async with AsyncSession(bind=connection, expire_on_commit=False) as session:
                org = Organization(name="cascade-org")
                session.add(org)
                await session.flush()
                pipeline = Pipeline(org_id=org.id, name="doomed_etl", source=PipelineSource.sdk)
                session.add(pipeline)
                await session.flush()
                channels = [
                    NotificationChannel(
                        org_id=org.id,
                        name=f"doomed-{index}",
                        url="https://hook.example.test/arbiter",
                        signing_secret="arbwhk_test",
                        enabled=True,
                    )
                    for index in range(2)
                ]
                session.add_all(channels)
                await session.flush()
                alert = Alert(
                    pipeline_id=pipeline.id,
                    type=AlertType.failure,
                    message="run failed",
                    resolved=False,
                )
                session.add(alert)
                await session.flush()
                session.add_all(
                    [
                        AlertDelivery(
                            alert_id=alert.id,
                            channel_id=channels[0].id,
                            status=AlertDeliveryStatus.pending,
                        ),
                        AlertDelivery(
                            alert_id=alert.id,
                            channel_id=channels[1].id,
                            status=AlertDeliveryStatus.delivered,
                        ),
                    ]
                )
                await session.commit()

                deleted = await pipeline_service.delete_pipeline(session, str(pipeline.id), org.id)

                assert deleted is True
                assert (await session.scalars(select(AlertDelivery))).all() == []
                assert (await session.scalars(select(Alert))).all() == []
    finally:
        await engine.dispose()


async def test_test_endpoint_probes_without_queuing(
    client, session, organization, auth_headers, monkeypatch
):
    endpoint = FakeEndpoint(204)
    monkeypatch.setattr(notification_service, "async_client_factory", endpoint)
    created = await create_channel(client, auth_headers, name="probe")

    response = await client.post(f"{CHANNELS_URL}/{created['id']}/test", headers=auth_headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["delivered"] is True
    assert body["status_code"] == 204
    assert body["error"] is None
    assert len(endpoint.calls) == 1
    assert await queue_of(session, organization) == []


async def test_disabling_a_channel_stops_new_deliveries(client, session, organization, auth_headers):
    created = await create_channel(client, auth_headers, name="quiet")

    response = await client.patch(
        f"{CHANNELS_URL}/{created['id']}", headers=auth_headers, json={"enabled": False}
    )
    assert response.status_code == 200
    assert response.json()["enabled"] is False

    await send_failed_run(client, auth_headers, pipeline="quiet_etl", run_id="quiet-1")

    assert await queue_of(session, organization) == []


async def test_channels_are_scoped_to_the_caller_organisation(
    client, session, organization, auth_headers
):
    from app.models.organization import Organization
    from app.models.pipeline import PipelineSource

    other = Organization(name=f"other_{uuid.uuid4().hex[:8]}")
    session.add(other)
    await session.commit()
    foreign_pipeline = Pipeline(
        org_id=other.id, name=f"foreign_{uuid.uuid4().hex[:8]}", source=PipelineSource.sdk
    )
    session.add(foreign_pipeline)
    await session.commit()
    await create_channel(client, auth_headers, name="mine")

    listed = await client.get(CHANNELS_URL, headers=auth_headers)
    assert [item["name"] for item in listed.json()] == ["mine"]
    assert (
        await client.delete(f"{CHANNELS_URL}/{uuid.uuid4()}", headers=auth_headers)
    ).status_code == 404
    refused = await client.patch(
        f"{CHANNELS_URL}/{foreign_pipeline.id}", headers=auth_headers, json={"enabled": False}
    )
    assert refused.status_code == 404


async def test_disabled_notifications_queue_nothing(
    client, session, organization, auth_headers, monkeypatch
):
    monkeypatch.setattr(settings, "notifications_enabled", False)
    await create_channel(client, auth_headers, name="off")
    await send_failed_run(client, auth_headers, pipeline="off_etl", run_id="off-1")

    assert await queue_of(session, organization) == []


async def test_more_channels_than_the_limit_is_rejected(client, auth_headers):
    for index in range(notification_service.MAX_CHANNELS_PER_ORG):
        await create_channel(client, auth_headers, name=f"c{index}", url=f"https://a.test/h{index}")

    response = await client.post(
        CHANNELS_URL,
        headers=auth_headers,
        json={"name": "one too many", "url": "https://a.test/extra"},
    )
    assert response.status_code == 400
    assert "at most" in response.json()["detail"]


async def test_deliveries_page_filters_by_status(client, session, organization, auth_headers, monkeypatch):
    endpoint = FakeEndpoint(200)
    monkeypatch.setattr(notification_service, "async_client_factory", endpoint)
    await create_channel(client, auth_headers, name="f1", url="https://a.test/1")
    await create_channel(client, auth_headers, name="f2", url="https://a.test/2")
    await send_failed_run(client, auth_headers, pipeline="filter_etl", run_id="filter-1")

    pending = await client.get(f"{CHANNELS_URL}/deliveries?status=pending", headers=auth_headers)
    assert pending.status_code == 200
    assert pending.json()["total"] == 2
    assert len({item["alert_id"] for item in pending.json()["items"]}) == 1

    await notification_service.deliver_due_alerts(session, org_id=organization.id)
    delivered = await client.get(f"{CHANNELS_URL}/deliveries?status=delivered", headers=auth_headers)
    assert delivered.json()["total"] == 2
    assert {item["status"] for item in delivered.json()["items"]} == {"delivered"}

    bad = await client.get(f"{CHANNELS_URL}/deliveries?status=nonsense", headers=auth_headers)
    assert bad.status_code == 422

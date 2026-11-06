from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.core.security import hash_password
from app.models.user import User

pytestmark = pytest.mark.asyncio


async def ingest_run(client, headers, *, pipeline, run_id, duration_ms, status="success", finished=True):
    """POST one run payload and return its row id."""
    finished_at = datetime.now(UTC)
    payload = {
        "pipeline": pipeline,
        "source": "sdk",
        "run_id": run_id,
        "status": status,
        "started_at": (finished_at - timedelta(milliseconds=duration_ms)).isoformat(),
        "duration_ms": duration_ms,
    }
    if finished:
        payload["finished_at"] = finished_at.isoformat()
    response = await client.post("/api/v1/runs", headers=headers, json=payload)
    assert response.status_code == 201
    return response.json()["id"]


async def duration_alerts(client, headers):
    """Return the active duration_exceeded alerts visible to this organisation."""
    response = await client.get("/api/v1/alerts?limit=200", headers=headers)
    assert response.status_code == 200
    return [alert for alert in response.json()["items"] if alert["type"] == "duration_exceeded"]


async def create_pipeline(client, headers, name, **fields):
    payload = {"name": name, "source": "sdk"}
    payload.update(fields)
    response = await client.post("/api/v1/pipelines", headers=headers, json=payload)
    assert response.status_code == 201
    return response.json()


async def test_explicit_threshold_creates_a_duration_alert(client, session, organization, auth_headers):
    pipeline = await create_pipeline(client, auth_headers, "slo-explicit", slow_threshold_ms=1000)
    assert pipeline["slow_threshold_ms"] == 1000

    await ingest_run(client, auth_headers, pipeline="slo-explicit", run_id="slow-1", duration_ms=5000)

    alerts = await duration_alerts(client, auth_headers)
    assert len(alerts) == 1
    assert "over the 1000ms budget" in alerts[0]["message"]
    assert alerts[0]["pipeline_id"] == pipeline["id"]


async def test_run_inside_explicit_threshold_creates_no_duration_alert(client, session, organization, auth_headers):
    await create_pipeline(client, auth_headers, "slo-inside", slow_threshold_ms=10_000)
    await ingest_run(client, auth_headers, pipeline="slo-inside", run_id="fast-1", duration_ms=500)

    assert await duration_alerts(client, auth_headers) == []


async def test_history_baseline_creates_a_duration_alert_without_a_threshold(
    client, session, organization, auth_headers
):
    await create_pipeline(client, auth_headers, "slo-baseline")
    for index, duration in enumerate((100, 200, 300, 400, 500)):
        await ingest_run(client, auth_headers, pipeline="slo-baseline", run_id=f"base-{index}", duration_ms=duration)

    await ingest_run(client, auth_headers, pipeline="slo-baseline", run_id="base-under", duration_ms=480)
    assert await duration_alerts(client, auth_headers) == []

    await ingest_run(client, auth_headers, pipeline="slo-baseline", run_id="base-over", duration_ms=5000)
    alerts = await duration_alerts(client, auth_headers)
    assert len(alerts) == 1
    assert "over the 500ms budget" in alerts[0]["message"]


async def test_thin_history_does_not_create_a_duration_alert(client, session, organization, auth_headers):
    await create_pipeline(client, auth_headers, "slo-thin")
    for index, duration in enumerate((100, 200)):
        await ingest_run(client, auth_headers, pipeline="slo-thin", run_id=f"thin-{index}", duration_ms=duration)
    await ingest_run(client, auth_headers, pipeline="slo-thin", run_id="thin-slow", duration_ms=5_000_000)

    assert await duration_alerts(client, auth_headers) == []


async def test_reingesting_a_run_does_not_duplicate_the_duration_alert(
    client, session, organization, auth_headers
):
    await create_pipeline(client, auth_headers, "slo-dedup", slow_threshold_ms=1000)
    await ingest_run(client, auth_headers, pipeline="slo-dedup", run_id="dup-1", duration_ms=5000)
    await ingest_run(client, auth_headers, pipeline="slo-dedup", run_id="dup-1", duration_ms=5000)

    assert len(await duration_alerts(client, auth_headers)) == 1


async def test_running_run_does_not_create_a_duration_alert(client, session, organization, auth_headers):
    await create_pipeline(client, auth_headers, "slo-running", slow_threshold_ms=1000)
    await ingest_run(
        client,
        auth_headers,
        pipeline="slo-running",
        run_id="running-1",
        duration_ms=90_000,
        status="running",
        finished=False,
    )

    assert await duration_alerts(client, auth_headers) == []


async def test_patch_updates_only_the_threshold(client, session, organization, auth_headers):
    pipeline = await create_pipeline(client, auth_headers, "slo-patch", slow_threshold_ms=2000)

    response = await client.patch(
        f"/api/v1/pipelines/{pipeline['id']}", headers=auth_headers, json={"slow_threshold_ms": 800}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["slow_threshold_ms"] == 800
    assert body["name"] == "slo-patch"

    response = await client.get(f"/api/v1/pipelines/{pipeline['id']}", headers=auth_headers)
    assert response.json()["slow_threshold_ms"] == 800


async def test_patch_null_clears_the_threshold(client, session, organization, auth_headers):
    pipeline = await create_pipeline(client, auth_headers, "slo-clear", slow_threshold_ms=1000)

    response = await client.patch(
        f"/api/v1/pipelines/{pipeline['id']}", headers=auth_headers, json={"slow_threshold_ms": None}
    )
    assert response.status_code == 200
    assert response.json()["slow_threshold_ms"] is None

    await ingest_run(client, auth_headers, pipeline="slo-clear", run_id="clear-1", duration_ms=50)
    await ingest_run(client, auth_headers, pipeline="slo-clear", run_id="clear-2", duration_ms=60)
    await ingest_run(client, auth_headers, pipeline="slo-clear", run_id="clear-3", duration_ms=5000)
    assert await duration_alerts(client, auth_headers) == []


@pytest.mark.parametrize("value", [0, -1])
async def test_patch_rejects_a_non_positive_threshold(client, session, organization, auth_headers, value):
    pipeline = await create_pipeline(client, auth_headers, "slo-invalid", slow_threshold_ms=1000)

    response = await client.patch(
        f"/api/v1/pipelines/{pipeline['id']}", headers=auth_headers, json={"slow_threshold_ms": value}
    )
    assert response.status_code == 422


async def test_patch_is_owner_only(client, session, organization, auth_headers):
    pipeline = await create_pipeline(client, auth_headers, "slo-role", slow_threshold_ms=1000)

    viewer = User(
        id=uuid.uuid4(),
        email=f"viewer+{uuid.uuid4().hex[:8]}@test.local",
        hashed_password=hash_password("testpass123"),
        role="viewer",
        org_id=organization.id,
    )
    session.add(viewer)
    await session.commit()

    response = await client.post(
        "/api/v1/auth/token", data={"username": viewer.email, "password": "testpass123"}
    )
    viewer_headers = {"Authorization": f"Bearer {response.json()['access_token']}"}

    response = await client.patch(
        f"/api/v1/pipelines/{pipeline['id']}", headers=viewer_headers, json={"slow_threshold_ms": 500}
    )
    assert response.status_code == 403


async def test_patch_unknown_pipeline_returns_404(client, session, organization, auth_headers):
    response = await client.patch(
        f"/api/v1/pipelines/{uuid.uuid4()}", headers=auth_headers, json={"slow_threshold_ms": 500}
    )
    assert response.status_code == 404

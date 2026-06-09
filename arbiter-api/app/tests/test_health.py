from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pipeline import Pipeline, PipelineSource, RunStatus
from app.models.pipeline_run import PipelineRun

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _create_pipeline(session: AsyncSession, org_id) -> Pipeline:
    pipeline = Pipeline(
        org_id=org_id,
        name=f"test-pipeline-{uuid.uuid4().hex[:8]}",
        source=PipelineSource.sdk,
    )
    session.add(pipeline)
    await session.commit()
    await session.refresh(pipeline)
    return pipeline


async def _create_run(
    session: AsyncSession,
    pipeline: Pipeline,
    *,
    status: RunStatus = RunStatus.success,
    started_at: datetime | None = None,
    run_id: str | None = None,
) -> PipelineRun:
    if started_at is None:
        started_at = datetime.now(UTC)
    run = PipelineRun(
        pipeline_id=pipeline.id,
        run_id=run_id or f"run-{uuid.uuid4().hex[:8]}",
        status=status,
        started_at=started_at,
        finished_at=started_at + timedelta(seconds=10),
        duration_ms=1000,
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return run


# ---------------------------------------------------------------------------
# /metrics/runs-per-day
# ---------------------------------------------------------------------------

async def test_runs_per_day_requires_auth(client):
    response = await client.get("/api/v1/metrics/runs-per-day")
    assert response.status_code in (401, 403)


async def test_runs_per_day_empty_db_returns_zeros(client, auth_headers):
    response = await client.get("/api/v1/metrics/runs-per-day?days=7", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["days"] == 7
    assert len(body["data"]) == 7
    for entry in body["data"]:
        assert entry["count"] == 0
        assert entry["failed"] == 0


async def test_runs_per_day_response_shape(client, auth_headers):
    response = await client.get("/api/v1/metrics/runs-per-day?days=3", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert "data" in body
    assert "days" in body
    assert body["days"] == 3
    for entry in body["data"]:
        assert "date" in entry
        assert "label" in entry
        assert "count" in entry
        assert "failed" in entry
        assert len(entry["date"]) == 10
        assert entry["date"][4] == "-" and entry["date"][7] == "-"


async def test_runs_per_day_counts_todays_runs(client, session, organization, auth_headers):
    pipeline = await _create_pipeline(session, organization.id)
    await _create_run(session, pipeline, status=RunStatus.success)
    await _create_run(session, pipeline, status=RunStatus.success)
    response = await client.get("/api/v1/metrics/runs-per-day?days=7", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    today_entry = body["data"][-1]
    assert today_entry["count"] >= 2


async def test_runs_per_day_failed_runs_counted_separately(client, session, organization, auth_headers):
    pipeline = await _create_pipeline(session, organization.id)
    await _create_run(session, pipeline, status=RunStatus.success)
    await _create_run(session, pipeline, status=RunStatus.failed)
    await _create_run(session, pipeline, status=RunStatus.failed)
    response = await client.get("/api/v1/metrics/runs-per-day?days=7", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    today_entry = body["data"][-1]
    assert today_entry["count"] >= 3
    assert today_entry["failed"] >= 2


async def test_runs_per_day_success_runs_dont_increment_failed(client, session, organization, auth_headers):
    pipeline = await _create_pipeline(session, organization.id)
    await _create_run(session, pipeline, status=RunStatus.success)
    response = await client.get("/api/v1/metrics/runs-per-day?days=1", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    today_entry = body["data"][-1]
    assert today_entry["failed"] == 0


async def test_runs_per_day_custom_days_param(client, auth_headers):
    for days in (1, 14, 30):
        response = await client.get(f"/api/v1/metrics/runs-per-day?days={days}", headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["days"] == days
        assert len(body["data"]) == days


async def test_runs_per_day_days_minimum_boundary(client, auth_headers):
    response = await client.get("/api/v1/metrics/runs-per-day?days=1", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]) == 1


async def test_runs_per_day_days_maximum_boundary(client, auth_headers):
    response = await client.get("/api/v1/metrics/runs-per-day?days=90", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]) == 90


async def test_runs_per_day_days_too_low_rejected(client, auth_headers):
    response = await client.get("/api/v1/metrics/runs-per-day?days=0", headers=auth_headers)
    assert response.status_code == 422


async def test_runs_per_day_days_too_high_rejected(client, auth_headers):
    response = await client.get("/api/v1/metrics/runs-per-day?days=91", headers=auth_headers)
    assert response.status_code == 422


async def test_runs_per_day_non_integer_days_rejected(client, auth_headers):
    response = await client.get("/api/v1/metrics/runs-per-day?days=abc", headers=auth_headers)
    assert response.status_code == 422


async def test_runs_per_day_gap_filling_zeros(client, session, organization, auth_headers):
    pipeline = await _create_pipeline(session, organization.id)
    six_days_ago = datetime.now(UTC) - timedelta(days=6)
    await _create_run(session, pipeline, started_at=six_days_ago)
    response = await client.get("/api/v1/metrics/runs-per-day?days=7", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    data = body["data"]
    assert len(data) == 7
    zero_entries = [e for e in data if e["count"] == 0]
    assert len(zero_entries) >= 5


async def test_runs_per_day_dates_are_ascending(client, session, organization, auth_headers):
    pipeline = await _create_pipeline(session, organization.id)
    await _create_run(session, pipeline)
    response = await client.get("/api/v1/metrics/runs-per-day?days=7", headers=auth_headers)
    assert response.status_code == 200
    dates = [entry["date"] for entry in response.json()["data"]]
    assert dates == sorted(dates)


async def test_runs_per_day_label_format(client, auth_headers):
    import re
    response = await client.get("/api/v1/metrics/runs-per-day?days=7", headers=auth_headers)
    assert response.status_code == 200
    for entry in response.json()["data"]:
        assert re.match(r"^[A-Z][a-z]{2} \d{2}$", entry["label"]), (
            f"Unexpected label format: {entry['label']!r}"
        )


async def test_runs_per_day_org_isolation(client, session, organization, auth_headers):
    from app.models.organization import Organization

    other_org = Organization(name="other-org-isolation")
    session.add(other_org)
    await session.commit()
    await session.refresh(other_org)

    other_pipeline = await _create_pipeline(session, other_org.id)
    await _create_run(session, other_pipeline, status=RunStatus.success)
    await _create_run(session, other_pipeline, status=RunStatus.failed)

    response = await client.get("/api/v1/metrics/runs-per-day?days=1", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    today_entry = body["data"][-1]
    assert today_entry["count"] == 0
    assert today_entry["failed"] == 0


async def test_runs_per_day_excludes_runs_outside_window(client, session, organization, auth_headers):
    pipeline = await _create_pipeline(session, organization.id)
    ten_days_ago = datetime.now(UTC) - timedelta(days=10)
    await _create_run(session, pipeline, started_at=ten_days_ago)
    response = await client.get("/api/v1/metrics/runs-per-day?days=7", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    total_count = sum(e["count"] for e in body["data"])
    assert total_count == 0


async def test_runs_per_day_default_days_is_seven(client, auth_headers):
    response = await client.get("/api/v1/metrics/runs-per-day", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["days"] == 7
    assert len(body["data"]) == 7

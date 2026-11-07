from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select

from app.models.alert import Alert, AlertType
from app.models.pipeline import Pipeline, PipelineSource
from app.services import alert_service

pytestmark = pytest.mark.asyncio


async def test_alert_listing_and_resolve(client, auth_headers):
    payload = {
        "pipeline": "demo-pipeline",
        "source": "sdk",
        "run_id": "run-alert-1",
        "status": "failed",
        "started_at": datetime.now(UTC).isoformat(),
        "finished_at": datetime.now(UTC).isoformat(),
        "duration_ms": 900,
        "error_message": "boom",
    }
    await client.post("/api/v1/runs", headers=auth_headers, json=payload)

    response = await client.get("/api/v1/alerts", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["items"]
    assert body["total"] >= 1

    alert_id = body["items"][0]["id"]
    response = await client.put(f"/api/v1/alerts/{alert_id}/resolve", headers=auth_headers)
    assert response.status_code == 200


async def test_resolve_alert_with_malformed_uuid_returns_404(client, auth_headers):
    response = await client.put("/api/v1/alerts/not-a-uuid/resolve", headers=auth_headers)
    assert response.status_code == 404


async def _seeded_pipeline(session, organization, name: str) -> Pipeline:
    pipeline = Pipeline(org_id=organization.id, name=name, source=PipelineSource.sdk)
    session.add(pipeline)
    await session.commit()
    return pipeline


async def test_a_second_open_no_run_alert_is_not_created(session, organization):
    pipeline = await _seeded_pipeline(session, organization, "no-run-dedupe")
    message = "No runs for pipeline no-run-dedupe in the last 24 hours"
    first = await alert_service.create_alert(
        session, pipeline_id=pipeline.id, alert_type=AlertType.no_run, message=message
    )
    second = await alert_service.create_alert(
        session, pipeline_id=pipeline.id, alert_type=AlertType.no_run, message=message
    )
    other = await alert_service.create_alert(
        session, pipeline_id=pipeline.id, alert_type=AlertType.no_run, message=message + " again"
    )
    await session.commit()

    assert first is not None
    assert second is None
    assert other is None
    total = await session.execute(
        select(func.count())
        .select_from(Alert)
        .where(Alert.type == AlertType.no_run, Alert.pipeline_id == pipeline.id)
    )
    assert total.scalar_one() == 1


async def test_a_resolved_no_run_alert_frees_the_slot(session, organization):
    pipeline = await _seeded_pipeline(session, organization, "no-run-after-resolve")
    message = "No runs for pipeline no-run-after-resolve in the last 24 hours"
    first = await alert_service.create_alert(
        session, pipeline_id=pipeline.id, alert_type=AlertType.no_run, message=message
    )
    first.resolved = True
    await session.commit()

    second = await alert_service.create_alert(
        session, pipeline_id=pipeline.id, alert_type=AlertType.no_run, message=message
    )
    await session.commit()

    assert second is not None
    open_alerts = await session.execute(
        select(func.count())
        .select_from(Alert)
        .where(
            Alert.type == AlertType.no_run,
            Alert.pipeline_id == pipeline.id,
            Alert.resolved.is_(False),
        )
    )
    assert open_alerts.scalar_one() == 1

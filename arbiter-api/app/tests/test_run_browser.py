from __future__ import annotations

from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import pytest

pytestmark = pytest.mark.asyncio

T0 = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)


async def ingest_run(
    client,
    headers,
    *,
    pipeline: str,
    run_id: str,
    run_status: str = "success",
    started_at: datetime = T0,
    error_message: str | None = None,
):
    """Send one run through the public ingest route and return the stored run."""
    response = await client.post(
        "/api/v1/runs",
        headers=headers,
        json={
            "pipeline": pipeline,
            "source": "sdk",
            "run_id": run_id,
            "status": run_status,
            "started_at": started_at.isoformat(),
            "finished_at": (started_at + timedelta(milliseconds=900)).isoformat(),
            "duration_ms": 900,
            "error_message": error_message,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


async def list_runs(client, headers, query: str = ""):
    response = await client.get(f"/api/v1/runs{query}", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


async def test_run_list_spans_every_pipeline_and_names_each_row(client, auth_headers):
    await ingest_run(client, auth_headers, pipeline="alpha_etl", run_id="alpha-1")
    await ingest_run(
        client, auth_headers, pipeline="beta_etl", run_id="beta-1", started_at=T0 + timedelta(hours=1)
    )

    page = await list_runs(client, auth_headers)

    assert page["total"] == 2
    assert [item["pipeline_name"] for item in page["items"]] == ["beta_etl", "alpha_etl"]
    assert page["items"][0]["run_id"] == "beta-1"
    assert page["items"][0]["pipeline_id"]


async def test_run_list_filters_by_status(client, auth_headers):
    await ingest_run(client, auth_headers, pipeline="alpha_etl", run_id="alpha-ok")
    await ingest_run(
        client,
        auth_headers,
        pipeline="alpha_etl",
        run_id="alpha-bad",
        run_status="failed",
        error_message="deadlock detected",
        started_at=T0 + timedelta(hours=1),
    )

    page = await list_runs(client, auth_headers, "?status=failed")

    assert page["total"] == 1
    assert [item["run_id"] for item in page["items"]] == ["alpha-bad"]


async def test_run_list_filters_by_pipeline(client, auth_headers):
    first = await ingest_run(client, auth_headers, pipeline="alpha_etl", run_id="alpha-1")
    await ingest_run(client, auth_headers, pipeline="beta_etl", run_id="beta-1")

    page = await list_runs(client, auth_headers, f"?pipeline_id={first['pipeline_id']}")

    assert page["total"] == 1
    assert [item["pipeline_name"] for item in page["items"]] == ["alpha_etl"]


async def test_run_list_searches_run_id_and_error_message(client, auth_headers):
    await ingest_run(client, auth_headers, pipeline="alpha_etl", run_id="scheduled__nightly")
    await ingest_run(
        client,
        auth_headers,
        pipeline="alpha_etl",
        run_id="scheduled__hourly",
        run_status="failed",
        error_message="Deadlock detected",
        started_at=T0 + timedelta(hours=1),
    )

    by_run_id = await list_runs(client, auth_headers, "?q=nightly")
    assert [item["run_id"] for item in by_run_id["items"]] == ["scheduled__nightly"]

    by_error = await list_runs(client, auth_headers, "?q=deadlock")
    assert [item["run_id"] for item in by_error["items"]] == ["scheduled__hourly"]

    nothing = await list_runs(client, auth_headers, "?q=missing")
    assert nothing == {"items": [], "total": 0, "limit": 20, "offset": 0}


async def test_run_list_filters_by_started_at_window(client, auth_headers):
    await ingest_run(client, auth_headers, pipeline="alpha_etl", run_id="day-1")
    day_2 = T0 + timedelta(days=1)
    await ingest_run(client, auth_headers, pipeline="alpha_etl", run_id="day-2", started_at=day_2)
    await ingest_run(
        client, auth_headers, pipeline="alpha_etl", run_id="day-3", started_at=T0 + timedelta(days=2)
    )

    page = await list_runs(
        client,
        auth_headers,
        f"?{urlencode({'started_from': day_2.isoformat(), 'started_to': day_2.isoformat()})}",
    )

    assert [item["run_id"] for item in page["items"]] == ["day-2"]

    from_page = await list_runs(client, auth_headers, f"?{urlencode({'started_from': day_2.isoformat()})}")
    assert from_page["total"] == 2


async def test_run_list_counts_the_filtered_rows(client, auth_headers):
    for offset in range(3):
        await ingest_run(
            client,
            auth_headers,
            pipeline="alpha_etl",
            run_id=f"run-{offset}",
            run_status="failed" if offset == 0 else "success",
            started_at=T0 + timedelta(hours=offset),
        )

    page = await list_runs(client, auth_headers, "?status=failed&limit=2")

    assert page["total"] == 1
    assert len(page["items"]) == 1
    assert page["limit"] == 2

    paged = await list_runs(client, auth_headers, "?limit=2&offset=2")
    assert paged["total"] == 3
    assert [item["run_id"] for item in paged["items"]] == ["run-0"]


async def test_run_list_hides_runs_of_other_organisations(client, session, auth_headers):
    from uuid import uuid4

    from app.models.organization import Organization
    from app.models.pipeline import Pipeline, PipelineSource, RunStatus
    from app.models.pipeline_run import PipelineRun

    other_org = Organization(id=uuid4(), name=f"other_{uuid4().hex[:8]}")
    other_pipeline = Pipeline(
        id=uuid4(), org_id=other_org.id, name="other_org_etl", source=PipelineSource.sdk
    )
    session.add(other_org)
    session.add(other_pipeline)
    await session.flush()
    session.add(
        PipelineRun(
            id=uuid4(),
            pipeline_id=other_pipeline.id,
            run_id="other-org-run",
            status=RunStatus.success,
            started_at=T0,
        )
    )
    await session.commit()

    page = await list_runs(client, auth_headers)

    assert page["total"] == 0


async def test_run_list_rejects_invalid_filters(client, auth_headers):
    for query in (
        "?status=nonsense",
        "?pipeline_id=not-a-uuid",
        "?started_from=not-a-date",
    ):
        response = await client.get(f"/api/v1/runs{query}", headers=auth_headers)
        assert response.status_code == 422, query


async def test_pipeline_list_filters_by_name_dag_id_and_status(client, auth_headers):
    await client.post(
        "/api/v1/pipelines",
        headers=auth_headers,
        json={"name": "nightly_report", "source": "airflow", "dag_id": "dag_report_2026"},
    )
    await ingest_run(client, auth_headers, pipeline="sales_import", run_id="sales-1", run_status="failed")

    by_name = await client.get("/api/v1/pipelines?q=nightly", headers=auth_headers)
    assert [item["name"] for item in by_name.json()["items"]] == ["nightly_report"]

    by_dag_id = await client.get("/api/v1/pipelines?q=DAG_REPORT", headers=auth_headers)
    assert by_dag_id.json()["total"] == 1

    by_status = await client.get("/api/v1/pipelines?status=failed", headers=auth_headers)
    assert [item["name"] for item in by_status.json()["items"]] == ["sales_import"]

    unfiltered = await client.get("/api/v1/pipelines", headers=auth_headers)
    assert unfiltered.json()["total"] == 2


async def test_alert_list_filters_by_type_resolved_and_pipeline(client, auth_headers):
    run = await ingest_run(
        client, auth_headers, pipeline="alpha_etl", run_id="alpha-bad", run_status="failed"
    )

    all_alerts = await client.get("/api/v1/alerts", headers=auth_headers)
    assert all_alerts.json()["total"] == 1
    alert = all_alerts.json()["items"][0]

    by_pipeline = await client.get(f"/api/v1/alerts?pipeline_id={run['pipeline_id']}", headers=auth_headers)
    assert by_pipeline.json()["total"] == 1

    other_pipeline = await client.get(
        "/api/v1/alerts?pipeline_id=00000000-0000-0000-0000-000000000001",
        headers=auth_headers,
    )
    assert other_pipeline.json()["total"] == 0

    by_type = await client.get("/api/v1/alerts?type=failure", headers=auth_headers)
    assert by_type.json()["total"] == 1
    silent_type = await client.get("/api/v1/alerts?type=no_run", headers=auth_headers)
    assert silent_type.json()["total"] == 0

    resolved = await client.put(f"/api/v1/alerts/{alert['id']}/resolve", headers=auth_headers)
    assert resolved.status_code == 200

    after_resolve = await client.get("/api/v1/alerts", headers=auth_headers)
    assert after_resolve.json()["total"] == 0

    history = await client.get("/api/v1/alerts?resolved=true", headers=auth_headers)
    assert history.json()["total"] == 1

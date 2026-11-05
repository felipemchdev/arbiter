from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio

from datetime import UTC, datetime


async def test_run_ingestion_and_fetch(client, auth_headers):
    payload = {
        "pipeline": "demo-pipeline",
        "source": "sdk",
        "run_id": "run-1",
        "status": "failed",
        "started_at": datetime.now(UTC).isoformat(),
        "finished_at": datetime.now(UTC).isoformat(),
        "duration_ms": 1234,
        "error_message": "boom",
        "tasks": [
            {
                "task_id": "extract",
                "status": "failed",
                "started_at": datetime.now(UTC).isoformat(),
                "finished_at": datetime.now(UTC).isoformat(),
                "duration_ms": 1000,
                "try_number": 1,
                "error_message": "boom",
            }
        ],
    }
    response = await client.post("/api/v1/runs", headers=auth_headers, json=payload)
    assert response.status_code == 201
    run_id = response.json()["id"]

    response = await client.get(f"/api/v1/runs/{run_id}", headers=auth_headers)
    assert response.status_code == 200

    response = await client.get(f"/api/v1/runs/{run_id}/tasks", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()[0]["task_id"] == "extract"


async def test_invalid_run_source_returns_422(client, auth_headers):
    response = await client.post(
        "/api/v1/runs",
        headers=auth_headers,
        json={
            "pipeline": "demo-pipeline",
            "source": "not-a-source",
            "run_id": "run-bad-source",
            "status": "success",
            "started_at": datetime.now(UTC).isoformat(),
        },
    )
    assert response.status_code == 422


async def test_invalid_task_status_returns_422(client, auth_headers):
    response = await client.post(
        "/api/v1/runs",
        headers=auth_headers,
        json={
            "pipeline": "demo-pipeline",
            "source": "sdk",
            "run_id": "run-bad-task-status",
            "status": "success",
            "started_at": datetime.now(UTC).isoformat(),
            "tasks": [
                {
                    "task_id": "extract",
                    "status": "exploded",
                    "started_at": datetime.now(UTC).isoformat(),
                }
            ],
        },
    )
    assert response.status_code == 422


async def test_rejected_run_is_not_persisted(client, session, organization, auth_headers):
    from app.models.pipeline_run import PipelineRun
    from sqlalchemy import select

    response = await client.post(
        "/api/v1/runs",
        headers=auth_headers,
        json={
            "pipeline": "atomicity-pipeline",
            "source": "sdk",
            "run_id": "run-atomicity-check",
            "status": "success",
            "started_at": datetime.now(UTC).isoformat(),
        },
    )
    assert response.status_code == 201

    response = await client.post(
        "/api/v1/runs",
        headers=auth_headers,
        json={
            "pipeline": "atomicity-pipeline",
            "source": "sdk",
            "run_id": "run-atomicity-check-2",
            "status": "nonsense",
            "started_at": datetime.now(UTC).isoformat(),
        },
    )
    assert response.status_code == 422

    stored = await session.execute(
        select(PipelineRun).where(PipelineRun.run_id == "run-atomicity-check-2")
    )
    assert stored.scalar_one_or_none() is None


async def test_run_tasks_accept_json_input_params(client, auth_headers):
    response = await client.post(
        "/api/v1/runs",
        headers=auth_headers,
        json={
            "pipeline": "input-params-pipeline",
            "source": "sdk",
            "run_id": "run-input-params",
            "status": "success",
            "started_at": datetime.now(UTC).isoformat(),
            "tasks": [
                {
                    "task_id": "extract",
                    "status": "success",
                    "started_at": datetime.now(UTC).isoformat(),
                    "input_params": {"batch": "2026-11-05"},
                }
            ],
        },
    )
    assert response.status_code == 201
    run_id = response.json()["id"]

    response = await client.get(f"/api/v1/runs/{run_id}/tasks", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()[0]["input_params"] == {"batch": "2026-11-05"}
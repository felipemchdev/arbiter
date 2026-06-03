from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio

from datetime import UTC, datetime


async def test_run_ingestion_and_fetch(client, auth_headers):
    payload = {
        "pipeline": "helios-eeip",
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
from __future__ import annotations

from datetime import UTC, datetime

import pytest

pytestmark = pytest.mark.asyncio



async def test_pipeline_lifecycle(client, session, organization, auth_headers):
    response = await client.post(
        "/api/v1/pipelines",
        headers=auth_headers,
        json={"name": "demo-pipeline", "source": "sdk", "dag_id": "dag-1"},
    )
    assert response.status_code == 201
    pipeline_id = response.json()["id"]

    response = await client.get("/api/v1/pipelines", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["items"][0]["name"] == "demo-pipeline"

    response = await client.get(f"/api/v1/pipelines/{pipeline_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "demo-pipeline"


async def test_pipeline_list_returns_pagination_envelope(client, session, organization, auth_headers):
    for name in ("pipeline-a", "pipeline-b", "pipeline-c"):
        response = await client.post(
            "/api/v1/pipelines",
            headers=auth_headers,
            json={"name": name, "source": "sdk"},
        )
        assert response.status_code == 201

    response = await client.get("/api/v1/pipelines?limit=2&offset=0", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"items", "total", "limit", "offset"}
    assert len(body["items"]) == 2
    assert body["limit"] == 2
    assert body["offset"] == 0
    assert body["total"] >= 3


async def test_pipeline_runs_list_returns_total(client, session, organization, auth_headers):
    response = await client.post(
        "/api/v1/pipelines",
        headers=auth_headers,
        json={"name": "runs-envelope-pipeline", "source": "sdk"},
    )
    pipeline_id = response.json()["id"]

    for run_id in ("run-env-1", "run-env-2"):
        response = await client.post(
            "/api/v1/runs",
            headers=auth_headers,
            json={
                "pipeline": "runs-envelope-pipeline",
                "source": "sdk",
                "run_id": run_id,
                "status": "success",
                "started_at": datetime.now(UTC).isoformat(),
            },
        )
        assert response.status_code == 201

    response = await client.get(f"/api/v1/pipelines/{pipeline_id}/runs", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 2
    assert len(body["items"]) == body["total"]

from __future__ import annotations

from datetime import UTC, datetime

import pytest

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

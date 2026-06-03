from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio

from datetime import UTC, datetime


async def test_alert_listing_and_resolve(client, auth_headers):
    payload = {
        "pipeline": "helios-eeip",
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
    assert response.json()

    alert_id = response.json()[0]["id"]
    response = await client.put(f"/api/v1/alerts/{alert_id}/resolve", headers=auth_headers)
    assert response.status_code == 200
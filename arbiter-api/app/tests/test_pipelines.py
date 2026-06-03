from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio

from app.tests.conftest import create_pipeline_fixture


async def test_pipeline_lifecycle(client, session, organization, auth_headers):
    response = await client.post(
        "/api/v1/pipelines",
        headers=auth_headers,
        json={"name": "helios-eeip", "source": "sdk", "dag_id": "dag-1"},
    )
    assert response.status_code == 201
    pipeline_id = response.json()["id"]

    response = await client.get("/api/v1/pipelines", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()[0]["name"] == "helios-eeip"

    response = await client.get(f"/api/v1/pipelines/{pipeline_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "helios-eeip"
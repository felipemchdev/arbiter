from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


async def test_token_and_api_key(client, organization, auth_headers):
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": organization.name, "password": organization._raw_api_key},  # type: ignore[attr-defined]
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    assert token

    response = await client.post("/api/v1/auth/api-key", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["api_key"].startswith("arb_")
from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


async def test_token_and_refresh_flow(client, owner_user):
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": owner_user.email, "password": owner_user._password},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


async def test_token_invalid_credentials(client):
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": "no@such.user", "password": "wrongpass"},
    )
    assert response.status_code == 401


async def test_refresh_and_logout(client, owner_user):
    login_resp = await client.post(
        "/api/v1/auth/token",
        data={"username": owner_user.email, "password": owner_user._password},
    )
    refresh_token = login_resp.json()["refresh_token"]

    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 200
    assert refresh_resp.json()["access_token"]
    assert refresh_resp.json()["refresh_token"]

    new_refresh = refresh_resp.json()["refresh_token"]
    logout_resp = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": new_refresh},
    )
    assert logout_resp.status_code == 200

    reused = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert reused.status_code == 401


async def test_api_key_crud(client, owner_user):
    login_resp = await client.post(
        "/api/v1/auth/token",
        data={"username": owner_user.email, "password": owner_user._password},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await client.post(
        "/api/v1/api-keys",
        headers=headers,
        json={"name": "Test Key", "environment": "development"},
    )
    assert create_resp.status_code == 200
    assert create_resp.json()["api_key"].startswith("arb_")
    key_id = create_resp.json()["id"]

    list_resp = await client.get("/api/v1/api-keys", headers=headers)
    assert list_resp.status_code == 200
    assert any(k["id"] == key_id for k in list_resp.json())

    revoke_resp = await client.post(f"/api/v1/api-keys/{key_id}/revoke", headers=headers)
    assert revoke_resp.status_code == 200

    delete_resp = await client.delete(f"/api/v1/api-keys/{key_id}", headers=headers)
    assert delete_resp.status_code == 200

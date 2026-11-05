from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.core.security import decode_access_token
from app.models.organization import Organization
from app.models.user import User
from app.services.auth_service import lookup_api_key

ADMIN_SCOPE = "org:admin"


async def get_db() -> AsyncIterator[AsyncSession]:
    async for session in get_session():
        yield session


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    return authorization.split(" ", 1)[1]


def parse_scopes(raw: str | None) -> set[str]:
    return {scope.strip() for scope in (raw or "").split(",") if scope.strip()}


def role_from_scopes(scopes: set[str]) -> str:
    return "owner" if ADMIN_SCOPE in scopes else "collector"


async def _user_from_access_token(db: AsyncSession, token: str) -> tuple[User, dict[str, Any]]:
    try:
        payload = decode_access_token(token)
    except Exception as exc:
        raise _unauthorized("invalid token") from exc

    sub = payload.get("sub")
    if not sub:
        raise _unauthorized("invalid token payload")
    try:
        user_id = UUID(sub)
    except ValueError:
        raise _unauthorized("invalid token payload")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise _unauthorized("user not found")

    # Access tokens embed the user's token_version; a password change bumps it and
    # invalidates every token issued before it, matching the refresh-token behaviour.
    try:
        token_version = int(payload.get("tv", 0))
    except (TypeError, ValueError):
        raise _unauthorized("invalid token payload")
    if token_version != user.token_version:
        raise _unauthorized("token revoked - re-login required")

    return user, payload


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> User:
    token = _bearer_token(authorization)
    if token is None:
        raise _unauthorized("bearer token required")
    if settings.auth_mode == "api_keys":
        raise _unauthorized("jwt authentication disabled by AUTH_MODE")
    user, _ = await _user_from_access_token(db, token)
    return user


async def get_current_org(
    request: Request,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> Organization:
    token = _bearer_token(authorization)
    if token is not None:
        if settings.auth_mode == "api_keys":
            raise _unauthorized("jwt authentication disabled by AUTH_MODE")
        user, payload = await _user_from_access_token(db, token)
        org_id = payload.get("org_id") or str(user.org_id)

        try:
            org_uuid = UUID(org_id)
        except (ValueError, TypeError):
            raise _unauthorized("invalid token payload")

        result = await db.execute(select(Organization).where(Organization.id == org_uuid))
        organization = result.scalar_one_or_none()
        if organization is None:
            raise _unauthorized("organization not found")

        organization._role = user.role or "viewer"
        organization._api_key_scopes = None
        return organization

    if x_api_key:
        if not settings.api_keys_enabled:
            raise _unauthorized("api key authentication disabled by API_KEYS_ENABLED")
        if settings.auth_mode == "jwt":
            raise _unauthorized("api key authentication disabled by AUTH_MODE")

        api_key = await lookup_api_key(db, x_api_key)
        if api_key is None:
            raise _unauthorized("invalid api key")

        api_key.last_used_at = datetime.now(UTC)
        api_key.last_used_ip = request.client.host if request.client else None
        api_key.last_used_user_agent = request.headers.get("user-agent", None)
        db.add(api_key)
        await db.commit()

        result = await db.execute(select(Organization).where(Organization.id == api_key.org_id))
        organization = result.scalar_one_or_none()
        if organization is None:
            raise _unauthorized("organization not found")

        scopes = parse_scopes(api_key.scopes)
        organization._role = role_from_scopes(scopes)
        organization._api_key_scopes = scopes
        return organization

    raise _unauthorized("missing authentication")

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import decode_access_token
from app.models.organization import Organization
from app.models.user import User
from app.services.auth_service import lookup_api_key


async def get_db() -> AsyncIterator[AsyncSession]:
    async for session in get_session():
        yield session


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="bearer token required")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token") from exc
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token payload")
    try:
        user_id = UUID(sub)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token payload")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found")
    return user


async def get_current_org(
    request: Request,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> Organization:
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
        try:
            payload = decode_access_token(token)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token") from exc

        org_id = payload.get("org_id") or payload.get("sub")
        if org_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token payload")

        result = await db.execute(select(Organization).where(Organization.id == UUID(org_id)))
        organization = result.scalar_one_or_none()
        if organization is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="organization not found")

        organization._role = payload.get("role", "viewer")
        return organization

    if x_api_key:
        api_key = await lookup_api_key(db, x_api_key)
        if api_key is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid api key")

        api_key.last_used_at = datetime.now(UTC)
        api_key.last_used_ip = request.client.host if request.client else None
        api_key.last_used_user_agent = request.headers.get("user-agent", None)
        db.add(api_key)
        await db.commit()

        result = await db.execute(select(Organization).where(Organization.id == api_key.org_id))
        organization = result.scalar_one_or_none()
        if organization is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="organization not found")

        organization._role = "owner"
        return organization

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing authentication")

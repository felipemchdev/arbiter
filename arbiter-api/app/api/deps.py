from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import decode_access_token, hash_api_key
from app.models.organization import Organization


async def get_db() -> AsyncIterator[AsyncSession]:
    async for session in get_session():
        yield session


async def get_current_org(
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> Organization:
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
        try:
            payload = decode_access_token(token)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token") from exc
        org_id = payload.get("sub")
        if org_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token payload")
        result = await db.execute(select(Organization).where(Organization.id == UUID(org_id)))
        organization = result.scalar_one_or_none()
        if organization is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="organization not found")
        return organization

    if x_api_key:
        hashed_api_key = hash_api_key(x_api_key)
        result = await db.execute(select(Organization).where(Organization.api_key == hashed_api_key))
        organization = result.scalar_one_or_none()
        if organization is not None:
            return organization
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid api key")

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing authentication")
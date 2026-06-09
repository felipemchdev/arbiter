from __future__ import annotations

import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_raw_api_key,
    hash_api_key,
    hash_refresh_token,
    verify_api_key,
    verify_password,
    verify_refresh_token,
)
from app.models.api_key import ApiKey
from app.models.organization import Organization
from app.models.refresh_token import RefreshToken
from app.models.user import User

logger = logging.getLogger(__name__)


async def authenticate_user(session: AsyncSession, email: str, password: str) -> User:
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    return user


def build_user_access_token(user: User) -> str:
    return create_access_token(sub=str(user.id), org_id=str(user.org_id), role=user.role)


async def build_refresh_token(session: AsyncSession, user: User) -> str:
    raw_token, expires_at = create_refresh_token()
    jti = str(uuid.uuid4())
    hashed = hash_refresh_token(raw_token)

    refresh = RefreshToken(
        user_id=user.id,
        jti=jti,
        hashed_token=hashed,
        expires_at=expires_at,
    )
    session.add(refresh)
    await session.commit()
    return f"{jti}.{raw_token}"


async def rotate_refresh_token(session: AsyncSession, old_refresh: RefreshToken) -> tuple[str, str]:
    old_refresh.revoked = True
    session.add(old_refresh)

    raw_token, expires_at = create_refresh_token()
    jti = str(uuid.uuid4())
    hashed = hash_refresh_token(raw_token)

    new_refresh = RefreshToken(
        user_id=old_refresh.user_id,
        jti=jti,
        hashed_token=hashed,
        expires_at=expires_at,
    )
    session.add(new_refresh)
    await session.commit()
    return f"{jti}.{raw_token}", jti


async def verify_and_consume_refresh_token(session: AsyncSession, token_str: str) -> tuple[User, RefreshToken]:
    from datetime import UTC, datetime

    now = datetime.now(UTC)

    # SQLite stores DateTime(timezone=True) as naive, so normalize for comparison
    def _ensure_aware(dt):
        if dt and dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt

    parts = token_str.split(".", 1)
    if len(parts) == 2:
        jti, raw_token = parts[0], parts[1]
        result = await session.execute(
            select(RefreshToken).where(RefreshToken.jti == jti)
        )
        rt = result.scalar_one_or_none()
        if rt is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid refresh token")
        if rt.revoked:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh token revoked")
        if _ensure_aware(rt.expires_at) < now:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh token expired")
        if not verify_refresh_token(raw_token, rt.hashed_token):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid refresh token")
    else:
        # Fallback: O(N) scan for legacy tokens without jti prefix
        result = await session.execute(select(RefreshToken))
        for rt in result.scalars():
            if rt.revoked:
                continue
            if _ensure_aware(rt.expires_at) < now:
                continue
            if verify_refresh_token(token_str, rt.hashed_token):
                break
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid refresh token")

    rt.last_used_at = now
    session.add(rt)
    await session.commit()

    user_result = await session.execute(select(User).where(User.id == rt.user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found")
    return user, rt


async def revoke_user_refresh_tokens(session: AsyncSession, user_id: uuid.UUID) -> None:
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.revoked == False)  # noqa: E712
    )
    for rt in result.scalars():
        rt.revoked = True
        session.add(rt)
    await session.commit()


async def create_api_key_entry(
    session: AsyncSession,
    org_id: uuid.UUID,
    name: str,
    environment: str,
    created_by: uuid.UUID | None = None,
    scopes: str = "collector:write",
) -> tuple[ApiKey, str]:
    raw_key = generate_raw_api_key(environment)
    prefix = raw_key[:12]
    hashed = hash_api_key(raw_key)

    api_key = ApiKey(
        org_id=org_id,
        name=name,
        environment=environment,
        prefix=prefix,
        hashed_key=hashed,
        scopes=scopes,
        created_by=created_by,
    )
    session.add(api_key)
    await session.commit()
    await session.refresh(api_key)
    logger.info("api_key_created", extra={"key_id": str(api_key.id), "org_id": str(org_id), "key_name": name})
    return api_key, raw_key


async def list_api_keys(session: AsyncSession, org_id: uuid.UUID) -> list[ApiKey]:
    result = await session.execute(select(ApiKey).where(ApiKey.org_id == org_id))
    return list(result.scalars().all())


async def revoke_api_key(session: AsyncSession, key_id: uuid.UUID, org_id: uuid.UUID) -> ApiKey:
    result = await session.execute(select(ApiKey).where(ApiKey.id == key_id, ApiKey.org_id == org_id))
    api_key = result.scalar_one_or_none()
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="api key not found")
    if api_key.revoked:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="api key already revoked")
    api_key.revoked = True
    session.add(api_key)
    await session.commit()
    await session.refresh(api_key)
    logger.info("api_key_revoked", extra={"key_id": str(api_key.id), "org_id": str(org_id)})
    return api_key


async def delete_api_key(session: AsyncSession, key_id: uuid.UUID, org_id: uuid.UUID) -> None:
    result = await session.execute(select(ApiKey).where(ApiKey.id == key_id, ApiKey.org_id == org_id))
    api_key = result.scalar_one_or_none()
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="api key not found")
    await session.delete(api_key)
    await session.commit()
    logger.info("api_key_deleted", extra={"key_id": str(key_id), "org_id": str(org_id)})


async def lookup_api_key(session: AsyncSession, raw_key: str) -> ApiKey | None:
    from datetime import UTC, datetime

    now = datetime.now(UTC)
    prefix = raw_key[:12] if len(raw_key) >= 12 else raw_key
    result = await session.execute(
        select(ApiKey).where(ApiKey.prefix == prefix, ApiKey.revoked == False)  # noqa: E712
    )
    for ak in result.scalars():
        if ak.expires_at is not None and ak.expires_at < now:
            continue
        if verify_api_key(raw_key, ak.hashed_key):
            return ak
    return None

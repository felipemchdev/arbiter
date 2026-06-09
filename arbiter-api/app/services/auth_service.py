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
    hash_password,
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
        token_version=user.token_version,
    )
    session.add(refresh)
    await session.commit()
    return f"{jti}.{raw_token}"


async def _lookup_refresh_token(session: AsyncSession, token_str: str) -> tuple[RefreshToken, str]:
    """Find and validate a refresh token. Returns (token_row, raw_token_part). Does NOT commit."""
    from datetime import UTC, datetime

    now = datetime.now(UTC)

    def _ensure_aware(dt):
        if dt and dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt

    parts = token_str.split(".", 1)
    if len(parts) == 2:
        jti, raw_token = parts[0], parts[1]
        result = await session.execute(select(RefreshToken).where(RefreshToken.jti == jti))
        rt = result.scalar_one_or_none()
        if rt is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid refresh token")
        if rt.revoked:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh token revoked")
        if _ensure_aware(rt.expires_at) < now:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh token expired")
        if not verify_refresh_token(raw_token, rt.hashed_token):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid refresh token")
        return rt, raw_token

    # Fallback: O(N) scan for legacy tokens without jti prefix
    result = await session.execute(select(RefreshToken))
    for rt in result.scalars():
        if rt.revoked:
            continue
        if _ensure_aware(rt.expires_at) < now:
            continue
        if verify_refresh_token(token_str, rt.hashed_token):
            return rt, token_str
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid refresh token")


async def verify_and_rotate_refresh_token(session: AsyncSession, token_str: str) -> tuple[User, str]:
    """Validate a refresh token, revoke it, issue a new one. Single commit."""
    from datetime import UTC, datetime

    now = datetime.now(UTC)

    old_rt, _ = await _lookup_refresh_token(session, token_str)
    old_rt.revoked = True
    old_rt.last_used_at = now
    session.add(old_rt)

    user_result = await session.execute(select(User).where(User.id == old_rt.user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found")

    if old_rt.token_version != user.token_version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token version mismatch - re-login required")

    raw_token, expires_at = create_refresh_token()
    jti = str(uuid.uuid4())
    hashed = hash_refresh_token(raw_token)
    new_rt = RefreshToken(
        user_id=user.id,
        jti=jti,
        hashed_token=hashed,
        expires_at=expires_at,
        token_version=user.token_version,
    )
    session.add(new_rt)
    await session.commit()

    return user, f"{jti}.{raw_token}"


async def consume_refresh_token(session: AsyncSession, token_str: str) -> User:
    """Validate a refresh token and mark it as used. Single commit. Used by logout."""
    from datetime import UTC, datetime

    rt, _ = await _lookup_refresh_token(session, token_str)

    user_result = await session.execute(select(User).where(User.id == rt.user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found")

    rt.last_used_at = datetime.now(UTC)
    session.add(rt)
    await session.commit()
    return user


async def change_password(session: AsyncSession, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="current password is incorrect")

    user.hashed_password = hash_password(new_password)
    user.token_version += 1
    session.add(user)

    result = await session.execute(
        select(RefreshToken).where(RefreshToken.user_id == user.id, RefreshToken.revoked == False)  # noqa: E712
    )
    for rt in result.scalars():
        rt.revoked = True
        session.add(rt)

    await session.commit()


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

    def _ensure_aware(dt):
        if dt and dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt

    now = datetime.now(UTC)
    prefix = raw_key[:12] if len(raw_key) >= 12 else raw_key
    result = await session.execute(
        select(ApiKey).where(ApiKey.prefix == prefix, ApiKey.revoked == False)  # noqa: E712
    )
    for ak in result.scalars():
        if ak.expires_at is not None and _ensure_aware(ak.expires_at) < now:
            continue
        if verify_api_key(raw_key, ak.hashed_key):
            return ak
    return None

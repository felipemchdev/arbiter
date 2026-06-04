from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (create_access_token, generate_raw_api_key, hash_api_key, verify_api_key, verify_password)
from app.models.organization import Organization
from app.models.user import User

logger = logging.getLogger(__name__)


async def authenticate_org(session: AsyncSession, organization_name: str, api_key: str) -> Organization:
    result = await session.execute(select(Organization).where(Organization.name == organization_name))
    organization = result.scalar_one_or_none()
    if organization is None or not verify_api_key(api_key, organization.api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    return organization


async def authenticate_user(session: AsyncSession, email: str, password: str) -> User:
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    return user


def build_access_token(organization: Organization) -> str:
    return create_access_token(sub=str(organization.id), org_id=str(organization.id), role="owner")


def build_user_access_token(user: User) -> str:
    return create_access_token(sub=str(user.id), org_id=str(user.org_id), role=user.role)


async def rotate_api_key(session: AsyncSession, organization: Organization) -> str:
    raw_api_key = generate_raw_api_key()
    organization.api_key = hash_api_key(raw_api_key)
    session.add(organization)
    await session.commit()
    await session.refresh(organization)
    logger.info("api_key_rotated", extra={"org_id": str(organization.id)})
    return raw_api_key

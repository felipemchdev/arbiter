from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, generate_raw_api_key, hash_api_key, verify_api_key
from app.models.organization import Organization

logger = logging.getLogger(__name__)


async def authenticate_org(session: AsyncSession, organization_name: str, api_key: str) -> Organization:
    result = await session.execute(select(Organization).where(Organization.name == organization_name))
    organization = result.scalar_one_or_none()
    if organization is None or not verify_api_key(api_key, organization.api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    return organization


def build_access_token(organization: Organization) -> str:
    return create_access_token(org_id=str(organization.id), org_name=organization.name)


async def rotate_api_key(session: AsyncSession, organization: Organization) -> str:
    raw_api_key = generate_raw_api_key()
    organization.api_key = hash_api_key(raw_api_key)
    session.add(organization)
    await session.commit()
    await session.refresh(organization)
    logger.info("api_key_rotated", extra={"org_id": str(organization.id)})
    return raw_api_key
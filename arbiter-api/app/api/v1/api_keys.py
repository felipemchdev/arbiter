from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_org, get_db
from app.api.role_guard import require_owner
from app.core.security import decode_access_token
from app.models.organization import Organization
from app.schemas.organization import ApiKeyCreateRequest, ApiKeyCreateResponse, ApiKeyRead
from app.services.auth_service import create_api_key_entry, delete_api_key, list_api_keys, revoke_api_key

router = APIRouter()


@router.get("", response_model=list[ApiKeyRead])
async def list_keys(
    current_org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    return await list_api_keys(db, current_org.id)


@router.post("", response_model=ApiKeyCreateResponse)
async def create_key(
    body: ApiKeyCreateRequest,
    current_org: Organization = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(default=None),
):
    created_by = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
        try:
            payload = decode_access_token(token)
            sub = payload.get("sub")
            if sub:
                created_by = UUID(sub)
        except Exception:
            pass
    api_key, raw_key = await create_api_key_entry(
        db,
        org_id=current_org.id,
        name=body.name,
        environment=body.environment,
        created_by=created_by,
    )
    return ApiKeyCreateResponse(api_key=raw_key, prefix=api_key.prefix, id=api_key.id)


@router.post("/{key_id}/revoke")
async def revoke_key(
    key_id: UUID,
    current_org: Organization = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    await revoke_api_key(db, key_id, current_org.id)
    return {"detail": "api key revoked"}


@router.delete("/{key_id}")
async def delete_key(
    key_id: UUID,
    current_org: Organization = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    await delete_api_key(db, key_id, current_org.id)
    return {"detail": "api key deleted"}

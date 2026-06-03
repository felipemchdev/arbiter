from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_org, get_db
from app.core.security import create_access_token
from app.schemas.organization import ApiKeyCreateResponse
from app.services.auth_service import authenticate_org, build_access_token, rotate_api_key

router = APIRouter()


@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    organization = await authenticate_org(db, form_data.username, form_data.password)
    return {"access_token": build_access_token(organization), "token_type": "bearer"}


@router.post("/api-key", response_model=ApiKeyCreateResponse)
async def create_api_key(
    current_org=Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    raw_api_key = await rotate_api_key(db, current_org)
    return ApiKeyCreateResponse(api_key=raw_api_key, org_id=current_org.id)
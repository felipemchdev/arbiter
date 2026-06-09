from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_org, get_db
from app.services.auth_service import (
    authenticate_user,
    build_refresh_token,
    build_user_access_token,
    revoke_user_refresh_tokens,
    rotate_refresh_token,
    verify_and_consume_refresh_token,
)

router = APIRouter()


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    refresh_token = await build_refresh_token(db, user)
    return {
        "access_token": build_user_access_token(user),
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    user, old_rt = await verify_and_consume_refresh_token(db, body.refresh_token)
    new_raw, _ = await rotate_refresh_token(db, old_rt)
    return {
        "access_token": build_user_access_token(user),
        "refresh_token": new_raw,
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    user, old_rt = await verify_and_consume_refresh_token(db, body.refresh_token)
    await revoke_user_refresh_tokens(db, user.id)
    return {"detail": "logged out"}

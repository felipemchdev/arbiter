from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from argon2 import PasswordHasher, Type
from argon2.exceptions import VerificationError
from jose import jwt

from app.core.config import settings

ALGORITHM = "HS256"
_argon2 = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4, hash_len=32, type=Type.ID)


def generate_raw_api_key(environment: str = "production") -> str:
    prefix = "arb_live" if environment == "production" else "arb_test"
    return f"{prefix}_{secrets.token_urlsafe(32)}"


def hash_api_key(raw_api_key: str) -> str:
    return _argon2.hash(raw_api_key)


def verify_api_key(raw_api_key: str, hashed_key: str) -> bool:
    try:
        return _argon2.verify(hashed_key, raw_api_key)
    except VerificationError:
        return False


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def hash_refresh_token(raw_token: str) -> str:
    return _argon2.hash(raw_token)


def verify_refresh_token(raw_token: str, hashed_token: str) -> bool:
    try:
        return _argon2.verify(hashed_token, raw_token)
    except VerificationError:
        return False


def hash_password(password: str) -> str:
    return _argon2.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _argon2.verify(hashed, plain)
    except VerificationError:
        return False


def create_access_token(*, sub: str, org_id: str, role: str = "viewer") -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": sub, "org_id": org_id, "role": role, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])


def create_refresh_token() -> tuple[str, datetime]:
    raw = generate_refresh_token()
    expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    return raw, expire

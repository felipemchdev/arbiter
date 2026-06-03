from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import jwt

from app.core.config import settings

ALGORITHM = "HS256"


def generate_raw_api_key() -> str:
    return f"arb_{secrets.token_urlsafe(32)}"


def hash_api_key(raw_api_key: str) -> str:
    return hashlib.sha256(raw_api_key.encode("utf-8")).hexdigest()


def verify_api_key(raw_api_key: str, hashed_api_key: str) -> bool:
    return hash_api_key(raw_api_key) == hashed_api_key


def create_access_token(*, org_id: str, org_name: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": org_id, "org_name": org_name, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
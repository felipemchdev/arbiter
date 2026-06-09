from __future__ import annotations

import logging
from functools import lru_cache
from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    project_name: str = "Arbiter"
    api_v1_str: str = "/api/v1"
    database_url: str = "sqlite+aiosqlite:///./arbiter.db"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    refresh_token_rotation_enabled: bool = True
    auth_mode: str = "jwt_api_keys"
    api_keys_enabled: bool = True
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    cors_origins: Union[str, List[str]] = "http://localhost:3000"
    stale_pipeline_hours: int = 24

    @field_validator("stale_pipeline_hours")
    @classmethod
    def _check_stale_hours(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("stale_pipeline_hours must be a positive integer")
        return v

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, list):
            normalized = []
            for item in v:
                if not isinstance(item, str):
                    raise ValueError(f"All CORS origins must be strings, got {type(item)}")
                stripped = item.strip()
                if stripped:
                    normalized.append(stripped)
            return normalized
        if isinstance(v, str):
            if not v.strip():
                return []
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("access_token_expire_minutes", "refresh_token_expire_days")
    @classmethod
    def _check_positive_ttl(cls, v: int, info) -> int:
        if v <= 0:
            raise ValueError(f"{info.field_name} must be a positive integer")
        return v

    @field_validator("auth_mode")
    @classmethod
    def _check_auth_mode(cls, v: str) -> str:
        if v not in ("jwt_api_keys", "jwt", "api_keys"):
            raise ValueError(f"invalid auth_mode '{v}'. allowed: jwt_api_keys, jwt, api_keys")
        return v

    def model_post_init(self, __context) -> None:
        if self.secret_key == "change-me-in-production":
            logger.warning("Using default SECRET_KEY - set ARBITER_SECRET_KEY env var for production.")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

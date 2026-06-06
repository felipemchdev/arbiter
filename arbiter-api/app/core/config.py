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
    access_token_expire_minutes: int = 1440
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    cors_origins: Union[str, List[str]] = "http://localhost:3000"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, list):
            normalized = []
            for item in v:
                if not isinstance(item, str):
                    raise TypeError(f"All CORS origins must be strings, got {type(item)}")
                stripped = item.strip()
                if stripped:
                    normalized.append(stripped)
            return normalized
        if isinstance(v, str):
            if not v.strip():
                return []
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    def model_post_init(self, __context) -> None:
        if self.secret_key == "change-me-in-production":
            logger.warning("Using default SECRET_KEY - set ARBITER_SECRET_KEY env var for production.")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

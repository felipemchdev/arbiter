from __future__ import annotations

import logging
from functools import lru_cache

from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client: Redis | None = None


@lru_cache
def _build_redis_client() -> Redis | None:
    try:
        return Redis.from_url(settings.redis_url, decode_responses=True)
    except (ValueError, OSError):
        logger.warning("redis_unavailable url=%s", settings.redis_url)
        return None


def get_redis() -> Redis | None:
    global _redis_client
    if _redis_client is None:
        _redis_client = _build_redis_client()
    return _redis_client

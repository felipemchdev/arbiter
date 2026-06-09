from __future__ import annotations

import logging
import time
from collections.abc import Callable

import redis.asyncio as aioredis
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._redis: aioredis.Redis | None = None
        self._disabled = False

    async def _get_redis(self) -> aioredis.Redis | None:
        if self._disabled:
            return None
        if self._redis is None:
            try:
                self._redis = aioredis.from_url(
                    settings.redis_url, decode_responses=True, socket_connect_timeout=3
                )
            except Exception:
                logger.warning("rate_limit_disabled redis_unavailable")
                self._disabled = True
                return None
        return self._redis

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        if request.url.path in ("/api/v1/health", "/api/v1/docs"):
            return await call_next(request)

        try:
            redis = await self._get_redis()
            if redis is None:
                return await call_next(request)

            client_ip = request.client.host if request.client else "unknown"
            key = f"ratelimit:{client_ip}"
            now = time.time()
            window_start = now - self.window_seconds

            pipe = redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            _, current = await pipe.execute()

            if current >= self.max_requests:
                return Response(
                    content='{"detail":"rate limit exceeded"}',
                    status_code=429,
                    media_type="application/json",
                )

            pipe = redis.pipeline()
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, self.window_seconds + 1)
            await pipe.execute()
        except Exception:
            logger.exception("rate_limit_failure path=%s", request.url.path)

        return await call_next(request)

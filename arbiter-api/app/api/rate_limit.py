from __future__ import annotations

import logging
import time
from functools import wraps

from fastapi import HTTPException, Request, status

from app.core.redis import get_redis

logger = logging.getLogger(__name__)


def _find_request(args, kwargs) -> Request | None:
    request = kwargs.get("request")
    if isinstance(request, Request):
        return request
    for arg in args:
        if isinstance(arg, Request):
            return arg
    return None


def rate_limit(max_requests: int = 60, window_seconds: int = 60):
    """Per-route limit backed by Redis so every worker process shares one budget.

    A module-level dict would be per-process: with several uvicorn workers or
    container replicas, a client could bypass the limit by spreading requests
    across processes. When Redis is unavailable the limit degrades to a no-op,
    matching RateLimitMiddleware.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = _find_request(args, kwargs)
            redis = get_redis()
            if redis is None or request is None:
                return await func(*args, **kwargs)

            host = request.client.host if request.client else "unknown"
            key = f"ratelimit:route:{host}:{request.url.path}"

            try:
                now = time.time()
                pipeline = redis.pipeline()
                pipeline.zremrangebyscore(key, 0, now - window_seconds)
                pipeline.zcard(key)
                _, current = await pipeline.execute()

                if current >= max_requests:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit exceeded: {max_requests} requests per {window_seconds}s",
                    )

                pipeline = redis.pipeline()
                pipeline.zadd(key, {str(now): now})
                pipeline.expire(key, window_seconds + 1)
                await pipeline.execute()
            except HTTPException:
                raise
            except Exception:  # noqa: BLE001 - rate limiting must never take the route down
                logger.warning("rate_limit_route_check_failed path=%s", request.url.path)

            return await func(*args, **kwargs)

        return wrapper

    return decorator

from __future__ import annotations

import logging
import time
import uuid
from functools import wraps

from fastapi import HTTPException, Request, status

from app.core.redis import get_redis

logger = logging.getLogger(__name__)


def _find_request(args, kwargs) -> Request | None:
    """Locate the FastAPI Request among the handler arguments.

    The limiter needs it for the client address and path. Handlers must declare a
    `request: Request` parameter, otherwise the check is skipped rather than
    silently limiting nobody.
    """
    request = kwargs.get("request")
    if isinstance(request, Request):
        return request
    for arg in args:
        if isinstance(arg, Request):
            return arg
    return None


async def record_and_check(redis, key: str, max_requests: int, window_seconds: int) -> bool:
    """Store one request in the sliding window and report whether it may proceed.

    Pruning, inserting, expiring and counting run in a single MULTI/EXEC, because
    a separate count step would let two concurrent requests read the same
    pre-insertion count and both pass a limit they share.

    The ZSET member carries a random suffix on purpose. Two requests in the same
    instant would otherwise collide on ``str(now)`` and count as one, which
    silently raises the effective limit.

    A request over the limit removes its own member, so a client that is throttled
    is not kept out by the requests it made while throttled.
    """
    now = time.time()
    member = f"{now}:{uuid.uuid4().hex}"

    pipeline = redis.pipeline()
    pipeline.zremrangebyscore(key, 0, now - window_seconds)
    pipeline.zadd(key, {member: now})
    pipeline.expire(key, window_seconds + 1)
    pipeline.zcard(key)
    replies = await pipeline.execute()
    current = int(replies[-1])

    if current <= max_requests:
        return True

    await redis.zrem(key, member)
    return False


def rate_limit(max_requests: int = 60, window_seconds: int = 60):
    """Per-route limit backed by Redis so every worker process shares one budget.

    A module-level dict would be per-process: with several uvicorn workers or
    container replicas, a client could bypass the limit by spreading requests
    across processes. When Redis is unavailable the limit degrades to a no-op,
    matching RateLimitMiddleware.
    """

    def decorator(func):
        """Wrap one route handler with this path's budget."""

        @wraps(func)
        async def wrapper(*args, **kwargs):
            """Count the call, then hand the handler the arguments it expects."""
            request = _find_request(args, kwargs)
            redis = get_redis()
            if redis is None or request is None:
                return await func(*args, **kwargs)

            host = request.client.host if request.client else "unknown"
            key = f"ratelimit:route:{host}:{request.url.path}"

            try:
                if not await record_and_check(redis, key, max_requests, window_seconds):
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit exceeded: {max_requests} requests per {window_seconds}s",
                    )
            except HTTPException:
                raise
            except Exception:  # noqa: BLE001 - rate limiting must never take the route down
                logger.warning("rate_limit_route_check_failed path=%s", request.url.path)

            return await func(*args, **kwargs)

        return wrapper

    return decorator

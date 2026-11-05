from __future__ import annotations

import logging
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.api.rate_limit import record_and_check
from app.core.redis import get_redis

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Give every route one shared per-client-IP budget.

    The window lives in Redis, so all worker processes and replicas count against
    the same budget. Routes can still add a tighter per-path limit with the
    ``rate_limit`` decorator.
    """

    def __init__(self, app: ASGIApp, max_requests: int = 100, window_seconds: int = 60):
        """Set the default budget; one client IP may make ``max_requests`` per window."""
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        """Count this request and answer 429 once the client IP is over budget.

        Health and docs stay uncounted so a container probe can never exhaust the
        budget of the process it checks. A Redis outage fails open: availability
        of the API outranks exact counting.
        """
        if request.url.path in ("/api/v1/health", "/api/v1/docs"):
            return await call_next(request)

        try:
            # Shared pool from app.core.redis: a second from_url() here would double
            # the connection count and drift from the rest of the app's Redis config.
            redis = get_redis()
            if redis is None:
                return await call_next(request)

            client_ip = request.client.host if request.client else "unknown"
            key = f"ratelimit:{client_ip}"

            if not await record_and_check(redis, key, self.max_requests, self.window_seconds):
                return Response(
                    content='{"detail":"rate limit exceeded"}',
                    status_code=429,
                    media_type="application/json",
                )
        except Exception:
            logger.exception("rate_limit_failure path=%s", request.url.path)

        return await call_next(request)

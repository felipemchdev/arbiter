from collections import defaultdict
import time
from functools import wraps

from fastapi import HTTPException, Request, status

# In-memory token bucket: { ip_or_key: [(timestamp, ...)] }
_requests: dict[str, list[float]] = defaultdict(list)


def rate_limit(max_requests: int = 60, window_seconds: int = 60):
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            key = request.client.host if request.client else "unknown"
            now = time.time()
            cutoff = now - window_seconds
            _requests[key] = [t for t in _requests.get(key, []) if t > cutoff]
            if len(_requests[key]) >= max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded: {max_requests} requests per {window_seconds}s",
                )
            _requests[key].append(now)
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

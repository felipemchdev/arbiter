from collections import defaultdict
import time
from functools import wraps

from fastapi import HTTPException, Request, status

_requests: dict[str, list[float]] = defaultdict(list)
_last_cleanup: float = time.time()


def rate_limit(max_requests: int = 60, window_seconds: int = 60):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            if request is None:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            path = request.url.path if request else "unknown"
            host = request.client.host if request and request.client else "unknown"
            key = f"{host}:{path}"
            now = time.time()
            cutoff = now - window_seconds

            global _last_cleanup
            if now - _last_cleanup > 60:
                stale = [k for k, v in _requests.items() if not v or max(v) < cutoff]
                for k in stale:
                    del _requests[k]
                _last_cleanup = now

            _requests[key] = [t for t in _requests.get(key, []) if t > cutoff]
            if len(_requests[key]) >= max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded: {max_requests} requests per {window_seconds}s",
                )
            _requests[key].append(now)
            return await func(*args, **kwargs)
        return wrapper
    return decorator

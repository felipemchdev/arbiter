"""Concurrency check for the shared rate-limit window, against a real Redis.

The fakes in test_runs.py prove the wiring; only a server proves that prune, insert
and count land in one MULTI/EXEC. Run it by exporting TEST_REDIS_URL, which CI does.
"""

from __future__ import annotations

import asyncio
import os
import uuid

import pytest

from app.api.rate_limit import record_and_check

pytestmark = pytest.mark.asyncio

REDIS_URL = os.environ.get("TEST_REDIS_URL", "")
MAX_REQUESTS = 30
CONCURRENT_CALLS = 60


async def test_shared_window_admits_exactly_max_requests_under_concurrency():
    """Sixty parallel callers of one budget must see thirty admitted, thirty refused."""
    if not REDIS_URL:
        pytest.skip("set TEST_REDIS_URL to exercise the limiter against a real Redis")

    from redis.asyncio import from_url

    client = from_url(REDIS_URL)
    key = f"ratelimit:test:{uuid.uuid4().hex}"
    try:
        decisions = await asyncio.gather(
            *(record_and_check(client, key, MAX_REQUESTS, 60) for _ in range(CONCURRENT_CALLS))
        )
        assert sum(decisions) == MAX_REQUESTS

        # A throttled caller must not consume budget: its member is removed again.
        window_size = await client.zcard(key)
        assert window_size == MAX_REQUESTS
    finally:
        await client.delete(key)
        await client.aclose()

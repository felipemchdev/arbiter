from __future__ import annotations

import queue
import threading
import time

import pytest

from arbiter.decorator import (
    MAX_QUEUE_SIZE,
    SHUTDOWN_JOIN_SECONDS,
    Arbiter,
    _BackgroundDispatcher,
    _RunPayload,
)
from arbiter.models import RunPayload


class DummyClient:
    def __init__(self) -> None:
        self.sent: list[_RunPayload] = []

    def send_run(self, payload) -> bool:
        self.sent.append(payload)
        return True


class BlockingClient:
    """Stops inside send_run until the test releases it."""

    def __init__(self) -> None:
        self.sent: list[_RunPayload] = []
        self.entered = threading.Event()
        self.release = threading.Event()

    def send_run(self, payload) -> bool:
        self.entered.set()
        self.release.wait(timeout=10)
        self.sent.append(payload)
        return True


def _payload() -> _RunPayload:
    return _RunPayload(
        pipeline="demo-pipeline",
        run_id="run-x",
        status="success",
        started_at="2026-11-05T00:00:00+00:00",
        finished_at="2026-11-05T00:00:01+00:00",
        duration_ms=1000,
        error_message=None,
    )


def test_monitor_returns_function_result():
    arbiter = Arbiter(api_key="arb_x", pipeline="demo-pipeline", api_url="http://localhost:8000")
    dummy = DummyClient()
    arbiter.client = dummy

    @arbiter.monitor
    def add(a, b):
        return a + b

    assert add(1, 2) == 3
    arbiter._get_dispatcher().shutdown()
    assert dummy.sent
    assert dummy.sent[0].pipeline == "demo-pipeline"


def test_monitor_run_ids_are_unique_within_the_same_second():
    arbiter = Arbiter(api_key="arb_x", pipeline="demo-pipeline", api_url="http://localhost:8000")
    dummy = DummyClient()
    arbiter.client = dummy

    @arbiter.monitor
    def add(a, b):
        return a + b

    for _ in range(25):
        add(1, 2)
    arbiter._get_dispatcher().shutdown()

    run_ids = [payload.run_id for payload in dummy.sent]
    assert len(run_ids) == 25
    assert len(set(run_ids)) == 25


def test_run_payload_generates_a_non_empty_run_id():
    first = RunPayload(pipeline="demo-pipeline", status="success", started_at="2026-11-05T00:00:00Z")
    second = RunPayload(pipeline="demo-pipeline", status="success", started_at="2026-11-05T00:00:00Z")
    assert first.run_id
    assert first.run_id != second.run_id


def test_shutdown_does_not_block_when_queue_is_full():
    """A parked worker and a full queue must still let shutdown return."""
    client = BlockingClient()
    dispatcher = _BackgroundDispatcher(client)
    try:
        # One payload parks the worker inside send_run, so the queue really fills.
        dispatcher._queue.put_nowait(_payload())
        assert client.entered.wait(1), "worker never reached the blocking send"
        for _ in range(MAX_QUEUE_SIZE):
            dispatcher._queue.put_nowait(_payload())
        assert dispatcher._queue.qsize() == MAX_QUEUE_SIZE
        with pytest.raises(queue.Full):
            dispatcher._queue.put_nowait(_payload())

        started = time.monotonic()
        dispatcher.shutdown()
        elapsed = time.monotonic() - started

        # The sentinel cannot be queued, so shutdown gives up after its join
        # timeout instead of blocking forever on a full queue.
        assert elapsed < SHUTDOWN_JOIN_SECONDS + 2
        assert dispatcher._worker.is_alive()
    finally:
        client.release.set()
        dispatcher._worker.join(timeout=5)
        assert not dispatcher._worker.is_alive()

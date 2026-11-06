from __future__ import annotations

import atexit
import functools
import logging
import queue
import threading
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx

logger = logging.getLogger(__name__)

MAX_QUEUE_SIZE = 1000
SHUTDOWN_POLL_SECONDS = 0.1
SHUTDOWN_JOIN_SECONDS = 5


@dataclass
class _RunPayload:
    pipeline: str
    run_id: str
    status: str
    started_at: str
    finished_at: str | None
    duration_ms: int | None
    error_message: str | None


class _Client:
    def __init__(self, api_url: str, api_key: str) -> None:
        self._api_url = api_url.rstrip("/")
        self._headers = {"X-API-Key": api_key, "Content-Type": "application/json"}

    def send_run(self, payload: _RunPayload) -> bool:
        try:
            resp = httpx.post(
                f"{self._api_url}/api/v1/runs",
                json={
                    "pipeline": payload.pipeline,
                    "source": "sdk",
                    "run_id": payload.run_id,
                    "status": payload.status,
                    "started_at": payload.started_at,
                    "finished_at": payload.finished_at,
                    "duration_ms": payload.duration_ms,
                    "error_message": payload.error_message,
                    "tasks": [],
                },
                headers=self._headers,
                timeout=10,
            )
            return resp.is_success
        except Exception:
            logger.exception("arbiter_send_failed")
            return False


class _BackgroundDispatcher:
    """Dispatches payloads via a daemon thread with graceful shutdown.

    Uses a queue + daemon thread instead of threading.Thread(target=...)
    created per-invocation, because Azure Functions can kill the host
    process between the time the decorator fires and the thread completes.
    Delivery is at most once: a send that fails or is rejected drops the
    payload, and a process killed before atexit runs can lose the queue.
    """

    def __init__(self, client: _Client) -> None:
        self._client = client
        self._queue: queue.Queue[_RunPayload | None] = queue.Queue(maxsize=MAX_QUEUE_SIZE)
        self._stopped = threading.Event()
        self._worker = threading.Thread(target=self._drain, daemon=True)
        self._worker.start()
        atexit.register(self.shutdown)

    def enqueue(self, payload: _RunPayload) -> None:
        try:
            self._queue.put_nowait(payload)
        except queue.Full:
            logger.warning("arbiter_queue_full dropping payload pipeline=%s", payload.pipeline)

    def _drain(self) -> None:
        while True:
            try:
                item = self._queue.get(timeout=SHUTDOWN_POLL_SECONDS)
            except queue.Empty:
                if self._stopped.is_set():
                    return
                continue
            if item is None:
                return
            self._client.send_run(item)

    def shutdown(self) -> None:
        # The queue is bounded, so a blocking put of the sentinel would hang shutdown
        # when it is full; the stop event lets the worker exit on its own instead.
        self._stopped.set()
        try:
            self._queue.put(None, timeout=SHUTDOWN_POLL_SECONDS)
        except queue.Full:
            pass
        self._worker.join(timeout=SHUTDOWN_JOIN_SECONDS)


class Arbiter:
    def __init__(self, *, api_key: str, pipeline: str, api_url: str = "http://localhost:8000") -> None:
        self.client = _Client(api_url, api_key)
        self.pipeline = pipeline
        self._dispatcher: _BackgroundDispatcher | None = None

    def _get_dispatcher(self) -> _BackgroundDispatcher:
        if self._dispatcher is None:
            self._dispatcher = _BackgroundDispatcher(self.client)
        return self._dispatcher

    def monitor(self, fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            started = datetime.now(UTC).isoformat()
            # Second-precision ids collide for concurrent runs of the same pipeline,
            # and the API upserts on (pipeline, run_id).
            run_id = f"sdk-{uuid.uuid4().hex}"
            try:
                result = fn(*args, **kwargs)
            except Exception as exc:
                finished = datetime.now(UTC).isoformat()
                self._get_dispatcher().enqueue(
                    _RunPayload(
                        pipeline=self.pipeline,
                        run_id=run_id,
                        status="failed",
                        started_at=started,
                        finished_at=finished,
                        duration_ms=None,
                        error_message=str(exc),
                    )
                )
                raise
            finished = datetime.now(UTC).isoformat()
            duration_ms = int(
                (datetime.fromisoformat(finished) - datetime.fromisoformat(started)).total_seconds() * 1000
            )
            self._get_dispatcher().enqueue(
                _RunPayload(
                    pipeline=self.pipeline,
                    run_id=run_id,
                    status="success",
                    started_at=started,
                    finished_at=finished,
                    duration_ms=duration_ms,
                    error_message=None,
                )
            )
            return result

        return wrapper

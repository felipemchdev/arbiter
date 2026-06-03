from __future__ import annotations

import functools
import logging
import threading
import traceback
from datetime import UTC, datetime
from uuid import uuid4

from arbiter.client import ArbiterClient
from arbiter.models import RunPayload

logger = logging.getLogger(__name__)


class Arbiter:
    def __init__(self, *, api_key: str, pipeline: str, api_url: str | None = None) -> None:
        import os

        self.client = ArbiterClient(
            api_key=api_key,
            pipeline=pipeline,
            api_url=api_url or os.getenv("ARBITER_API_URL", "http://localhost:8000"),
        )
        self.pipeline = pipeline

    def monitor(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            run_id = str(uuid4())
            started_at = datetime.now(UTC)
            status = "success"
            error_message = None
            result = None
            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                status = "failed"
                error_message = traceback.format_exc()
                raise
            finally:
                finished_at = datetime.now(UTC)
                payload = RunPayload(
                    pipeline=self.pipeline,
                    run_id=run_id,
                    source="sdk",
                    status=status,
                    started_at=started_at,
                    finished_at=finished_at,
                    duration_ms=int((finished_at - started_at).total_seconds() * 1000),
                    error_message=error_message,
                )
                threading.Thread(target=self._send_payload, args=(payload,), daemon=True).start()

        return wrapper

    def _send_payload(self, payload: RunPayload) -> None:
        try:
            self.client.send_run(payload)
        except Exception as exc:  # noqa: BLE001
            logger.warning("arbiter_monitor_send_failed", extra={"error": str(exc), "pipeline": self.pipeline})
from __future__ import annotations

import logging

import httpx

from arbiter.exceptions import ArbiterError
from arbiter.models import RunPayload

logger = logging.getLogger(__name__)


class ArbiterClient:
    def __init__(self, *, api_key: str, pipeline: str, api_url: str) -> None:
        self.api_key = api_key
        self.pipeline = pipeline
        self.api_url = api_url.rstrip("/")

    def send_run(self, payload: RunPayload) -> None:
        headers = {"X-API-Key": self.api_key}
        try:
            response = httpx.post(f"{self.api_url}/api/v1/runs", json=payload.model_dump(mode="json"), headers=headers, timeout=5.0)
            response.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            logger.warning("arbiter_run_send_failed", extra={"error": str(exc), "pipeline": self.pipeline})
            raise ArbiterError(str(exc)) from exc
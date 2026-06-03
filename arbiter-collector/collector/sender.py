from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)


class ArbiterSender:
    def __init__(self, api_url: str, api_key: str) -> None:
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key

    def send(self, payload: dict) -> None:
        try:
            response = httpx.post(
                f"{self.api_url}/api/v1/collector/airflow/sync",
                json=payload,
                headers={"X-API-Key": self.api_key},
                timeout=30.0,
            )
            response.raise_for_status()
            result = response.json()
            logger.info("collector_send_ok ingested=%d", result.get("ingested", 0))
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "collector_send_http_error status=%d body=%s",
                exc.response.status_code,
                exc.response.text[:500],
            )
        except Exception as exc:
            logger.warning("collector_send_failed error=%s", exc)

from __future__ import annotations

from dataclasses import dataclass

import httpx


@dataclass
class AirflowClient:
    base_url: str
    username: str
    password: str

    def _client(self) -> httpx.Client:
        if not hasattr(self, "_cached_client"):
            self._cached_client = httpx.Client(
                base_url=self.base_url.rstrip("/"),
                auth=(self.username, self.password),
                timeout=15.0,
            )
        return self._cached_client

    def close(self) -> None:
        if hasattr(self, "_cached_client") and self._cached_client is not None:
            self._cached_client.close()
            self._cached_client = None

    def get_dags(self) -> list[dict]:
        client = self._client()
        response = client.get("/api/v1/dags")
        response.raise_for_status()
        data = response.json()
        dags = data.get("dags", data if isinstance(data, list) else [])
        return [d for d in dags if not d.get("is_paused", False)]

    def get_runs(self, dag_id: str, limit: int = 5) -> list[dict]:
        client = self._client()
        response = client.get(
            f"/api/v1/dags/{dag_id}/dagRuns",
            params={"limit": limit, "order_by": "-start_date"},
        )
        response.raise_for_status()
        data = response.json()
        return data.get("dag_runs", [])

    def get_tasks(self, dag_id: str) -> list[dict]:
        client = self._client()
        response = client.get(f"/api/v1/dags/{dag_id}/tasks")
        response.raise_for_status()
        data = response.json()
        return data.get("tasks", data if isinstance(data, list) else [])

    def get_task_instances(self, dag_id: str, run_id: str) -> list[dict]:
        client = self._client()
        response = client.get(
            f"/api/v1/dags/{dag_id}/dagRuns/{run_id}/taskInstances",
        )
        response.raise_for_status()
        data = response.json()
        return data.get("task_instances", [])

    def get_edges(self, dag_id: str, tasks: list[dict]) -> list[dict]:
        edges: list[dict] = []
        for task in tasks:
            task_id = task.get("task_id") or task.get("id", "")
            if not task_id:
                continue
            downstream = task.get("downstream_task_ids", [])
            for target_id in downstream:
                edges.append({"source": task_id, "target": target_id})
        return edges

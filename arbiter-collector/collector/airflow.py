from __future__ import annotations

from dataclasses import dataclass

import httpx


@dataclass
class AirflowClient:
    base_url: str
    username: str
    password: str

    def _client(self) -> httpx.Client:
        return httpx.Client(base_url=self.base_url.rstrip("/"), auth=(self.username, self.password), timeout=10.0)

    def get_dags(self) -> list[dict]:
        with self._client() as client:
            response = client.get("/api/v1/dags")
            response.raise_for_status()
            return response.json().get("dags", [])

    def get_runs(self, dag_id: str, limit: int = 5) -> list[dict]:
        with self._client() as client:
            response = client.get(f"/api/v1/dags/{dag_id}/dagRuns", params={"limit": limit})
            response.raise_for_status()
            return response.json().get("dag_runs", response.json().get("dagRuns", []))

    def get_tasks(self, dag_id: str) -> list[dict]:
        with self._client() as client:
            response = client.get(f"/api/v1/dags/{dag_id}/tasks")
            response.raise_for_status()
            data = response.json()
            return data.get("tasks", data.get("nodes", []))

    def get_task_instances(self, dag_id: str, run_id: str) -> list[dict]:
        with self._client() as client:
            response = client.get(f"/api/v1/dags/{dag_id}/dagRuns/{run_id}/taskInstances")
            response.raise_for_status()
            return response.json().get("task_instances", response.json().get("taskInstances", []))
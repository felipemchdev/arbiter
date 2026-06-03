from __future__ import annotations

import argparse
import logging
import time

from collector.airflow import AirflowClient
from collector.config import settings
from collector.sender import ArbiterSender

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


def build_payload(airflow_client: AirflowClient) -> dict:
    dags_payload: list[dict] = []
    for dag in airflow_client.get_dags():
        dag_id = dag.get("dag_id") or dag.get("id")
        if not dag_id:
            continue

        runs_payload: list[dict] = []
        for run in airflow_client.get_runs(dag_id, limit=5):
            run_id = run.get("run_id") or run.get("dag_run_id") or run.get("id")
            if not run_id:
                continue
            task_instances = airflow_client.get_task_instances(dag_id, run_id)
            runs_payload.append(
                {
                    "run_id": run_id,
                    "status": run.get("state") or run.get("status", "running"),
                    "started_at": run.get("start_date") or run.get("started_at"),
                    "finished_at": run.get("end_date") or run.get("finished_at"),
                    "duration_ms": run.get("duration_ms"),
                    "error_message": run.get("error_message"),
                    "tasks": [
                        {
                            "task_id": ti.get("task_id") or ti.get("id", ""),
                            "status": ti.get("state") or ti.get("status", "running"),
                            "started_at": ti.get("start_date") or ti.get("started_at"),
                            "finished_at": ti.get("end_date") or ti.get("finished_at"),
                            "duration_ms": ti.get("duration_ms") or ti.get("duration"),
                            "try_number": ti.get("try_number", 1),
                            "log_url": ti.get("log_url"),
                            "error_message": ti.get("error_message"),
                        }
                        for ti in task_instances
                    ],
                }
            )

        tasks = airflow_client.get_tasks(dag_id)
        nodes = [
            {"id": t.get("task_id") or t.get("id", ""), "label": t.get("task_id") or t.get("id", ""), "type": "task"}
            for t in tasks
        ]
        edges = airflow_client.get_edges(dag_id, tasks)

        dags_payload.append(
            {
                "dag_id": dag_id,
                "name": dag.get("dag_display_name") or dag.get("dag_id", dag_id),
                "nodes": nodes,
                "edges": edges,
                "runs": runs_payload,
            }
        )
    return {"dags": dags_payload}


def run_loop(
    airflow_url: str,
    airflow_user: str,
    airflow_pass: str,
    arbiter_api: str,
    arbiter_key: str,
    interval: int,
) -> None:
    airflow_client = AirflowClient(airflow_url, airflow_user, airflow_pass)
    sender = ArbiterSender(arbiter_api, arbiter_key)
    logger.info("collector_started interval=%d", interval)
    while True:
        logger.info("collector_poll_start")
        payload = build_payload(airflow_client)
        sender.send(payload)
        time.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(prog="arbiter-collector")
    parser.add_argument("--airflow-url", default=settings.airflow_url)
    parser.add_argument("--airflow-user", default=settings.airflow_user)
    parser.add_argument("--airflow-pass", default=settings.airflow_pass)
    parser.add_argument("--arbiter-api", default=settings.arbiter_api)
    parser.add_argument("--arbiter-key", default=settings.arbiter_key)
    parser.add_argument("--interval", type=int, default=settings.collector_interval)

    args = parser.parse_args()
    run_loop(args.airflow_url, args.airflow_user, args.airflow_pass, args.arbiter_api, args.arbiter_key, args.interval)


if __name__ == "__main__":
    main()

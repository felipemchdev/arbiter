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
    dags_payload = []
    for dag in airflow_client.get_dags():
        dag_id = dag.get("dag_id") or dag.get("id")
        runs_payload = []
        for run in airflow_client.get_runs(dag_id, limit=5):
            run_id = run.get("run_id") or run.get("id")
            runs_payload.append(
                {
                    "run_id": run_id,
                    "status": run.get("state", run.get("status", "running")),
                    "started_at": run.get("start_date") or run.get("started_at"),
                    "finished_at": run.get("end_date") or run.get("finished_at"),
                    "duration_ms": run.get("duration_ms"),
                    "error_message": run.get("error_message"),
                    "tasks": airflow_client.get_task_instances(dag_id, run_id),
                }
            )
        dags_payload.append(
            {
                "dag_id": dag_id,
                "name": dag.get("dag_display_name") or dag.get("dag_id"),
                "nodes": [{"id": task.get("task_id") or task.get("id"), "label": task.get("task_id") or task.get("id"), "type": "task"} for task in airflow_client.get_tasks(dag_id)],
                "edges": [],
                "runs": runs_payload,
            }
        )
    return {"dags": dags_payload}


def run(args: argparse.Namespace) -> None:
    airflow_client = AirflowClient(args.airflow_url, args.airflow_user, args.airflow_pass)
    sender = ArbiterSender(args.arbiter_api, args.arbiter_key)
    while True:
        logger.info("collector_poll_start")
        sender.send(build_payload(airflow_client))
        time.sleep(args.interval)


def main() -> None:
    parser = argparse.ArgumentParser(prog="arbiter-collector")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("--airflow-url", default=settings.airflow_url)
    start_parser.add_argument("--airflow-user", default=settings.airflow_user)
    start_parser.add_argument("--airflow-pass", default=settings.airflow_pass)
    start_parser.add_argument("--arbiter-api", default=settings.arbiter_api)
    start_parser.add_argument("--arbiter-key", default=settings.arbiter_key)
    start_parser.add_argument("--interval", type=int, default=settings.collector_interval)

    args = parser.parse_args()
    if args.command == "start":
        run(args)


if __name__ == "__main__":
    main()
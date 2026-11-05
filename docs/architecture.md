# Arbiter Architecture

## System Overview

Arbiter is an observability tool for data pipeline runs. It does not start,
schedule or run your jobs. Another system runs them.

An external system sends one event per run to the API over HTTP. Each event
contains the pipeline, the DAG and the task instances of that run. The API
stores the event and computes the status, the duration and the alerts for it.
The dashboard reads that data and shows DAG diagrams, metrics, task timelines
and alerts.

## Components

| Component | Language | Port | Function |
|---|---|---|---|
| arbiter-api | Python/FastAPI | 8000 | Stores runs, checks users, serves data |
| arbiter-dashboard | TypeScript/Next.js | 3000 | Shows DAGs, timelines, metrics, the run browser and alerts |
| arbiter-worker | Python/Celery | - | Runs `check_stale_pipelines` every 10 minutes |
| arbiter-redis | Redis 7 | 6379 | Holds the Celery queue and the task results |
| PostgreSQL or SQLite | SQL | 5432 | Stores all Arbiter data |

Use PostgreSQL in Docker and in production. SQLite is for a local run only.

## Data Flow

1. An external system sends run data to `POST /api/v1/runs/ingest`.
2. The API writes the pipeline, the run, the tasks and the DAG to the database
   in one transaction.
3. In the same request, `process_run_event_sync` sets `duration_ms` and
   `last_run_status`.
4. That task creates a `failure` alert when a task in the run failed.
5. The dashboard reads the data from the API with `GET /api/v1/*`.
6. Every 10 minutes, Celery Beat runs `check_stale_pipelines`. That task finds
   pipelines with no run in `STALE_PIPELINE_HOURS` hours and creates a `no_run`
   alert for each of them.

## Alerts

The API creates two alert types:

- `failure` - a task in the run failed.
- `no_run` - the pipeline had no run inside the stale window.

The `AlertType` enum also has `duration_exceeded`. No code creates that alert
today.

An owner can resolve an alert in the dashboard or with
`PUT /api/v1/alerts/:id/resolve`.

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
| arbiter-dashboard | TypeScript/Next.js | 3000 | Shows DAGs, timelines, metrics, the run browser, alerts and notification channels |
| arbiter-worker | Python/Celery | - | Runs `check_stale_pipelines` every 10 minutes and `deliver_pending_alerts` every minute |
| arbiter-redis | Redis 7 | 6379 | Holds the Celery queue and the task results |
| PostgreSQL or SQLite | SQL | 5432 | Stores all Arbiter data |

Use PostgreSQL in Docker and in production. SQLite is for a local run only.

## Data Flow

1. An external system sends run data to `POST /api/v1/runs/ingest`.
2. The API writes the pipeline, the run, the tasks and the DAG to the database
   in one transaction.
3. In the same request, `process_run_event_sync` sets `duration_ms` and
   `last_run_status`.
4. That step creates a `failure` alert when the run failed.
5. The same step compares `duration_ms` with the pipeline budget. It creates a
   `duration_exceeded` alert when the run is longer.
6. Each new alert writes one delivery row per active channel, in the same
   transaction.
7. The dashboard reads the data from the API with `GET /api/v1/*`.
8. Every 10 minutes, Celery Beat runs `check_stale_pipelines`. That task finds
   pipelines with no run in `STALE_PIPELINE_HOURS` hours and creates a `no_run`
   alert for each of them.
9. Every minute, Celery Beat runs `deliver_pending_alerts`. That task posts
   each due delivery row to its channel and stores the answer.

## Alerts

The API creates three alert types:

- `failure` - the run failed.
- `duration_exceeded` - the run took longer than its budget.
- `no_run` - the pipeline had no run inside the stale window.

The budget for a pipeline is `slow_threshold_ms`, when an owner sets it.
Without that value the API uses the 95th percentile of the last
`DURATION_BASELINE_SAMPLES` successful runs of the same pipeline. It creates no
alert until it has `DURATION_BASELINE_MIN_SAMPLES` of those runs. A short run
history is not an anomaly.

An owner can resolve an alert in the dashboard or with
`PUT /api/v1/alerts/:id/resolve`.

## Alert Notifications

An alert is not enough on its own: a person has to open the dashboard to see
it. Arbiter therefore posts each new alert to every webhook channel that an
owner registers.

- The API writes the delivery rows in the alert transaction, so a stored alert
  always gets a send and a rolled back ingest leaves nothing behind. See
  `docs/adr.md`, ADR-002.
- The worker signs each body with HMAC-SHA256, so the receiver can check that
  the request came from Arbiter.
- A delivery that keeps failing stops after `NOTIFICATION_MAX_ATTEMPTS`
  attempts. The row keeps the last error and the last status code.
- Deleting a channel also removes its queued rows. Alerts stay in the database.

`docs/api-integration.md` documents the payload, the headers and the signature
check.

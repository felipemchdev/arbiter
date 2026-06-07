# Arbiter Architecture

## System Overview

Arbiter is an ingest-first observability platform for data pipeline runs.
It receives run events (pipelines, DAGs, tasks) via HTTP and provides a
dashboard with DAG visualization, metrics, and alerts.

## Components

| Component | Language | Port | Purpose |
|---|---|---|---|
| arbiter-api | Python/FastAPI | 8000 | Core API, ingestion, auth |
| arbiter-dashboard | TypeScript/Next.js | 3000 | UI with DAG, timeline, metrics |
| arbiter-worker | Python/Celery | — | Scheduled stale-pipeline detection |
| arbiter-redis | Redis 7 | 6379 | Celery broker and result backend |
| PostgreSQL | SQL | 5432 | Primary data store |

## Data Flow

External system → POST /api/v1/runs/ingest → arbiter-api → PostgreSQL
                                                    ↓
                                          process_run_event_sync (inline)
                                                    ↓
                                          update pipeline, create alerts
                                                    ↓
arbiter-dashboard → GET /api/v1/* → arbiter-api → PostgreSQL

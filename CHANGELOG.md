# Changelog

All notable changes to Arbiter are documented in this file.

## [0.1.0] — Unreleased

### Added
- Pipeline observability dashboard (Next.js 14)
- FastAPI backend with async SQLAlchemy 2.0
- DAG visualization via ReactFlow
- Task timeline (Gantt-style)
- Alert system (failure, no_run, duration_exceeded)
- Celery worker + Beat scheduler
- Docker Compose development environment
- Alembic migrations
- Configurable CORS
- Rate limiting on ingest endpoints
- Per-pipeline duration budget (`slow_threshold_ms`) and the `duration_exceeded` alert
- Run browser with status, pipeline, date-window and free-text filters
- Filters on the run, pipeline and alert list endpoints
- Notification channels with HMAC-signed webhook delivery, retries and backoff
- Alert delivery records (outbox) and a delivery view in the dashboard

### Changed
- Endpoint migration: `/collector/airflow/sync` → `/runs/ingest`
- Credentials: OSS defaults use `admin`/`viewer` with `arbiter26@`

### Fixed
- Server component event handler crash in production (button-arbiter)
- SQLAlchemy `else_` → `default` in `func.case()`
- Seeds guard via `RUN_SEEDS` env var
- CORS from hardcoded to `CORS_ORIGINS` env var
- PostgreSQL: revision 0001 created every enum type twice, so `alembic upgrade head`
  failed on an empty database
- Baseline adoption now checks the unique guards of revisions 0002 and 0003 before it
  stamps a schema

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
- Baseline adoption now checks the uniqueness guards of revisions 0002 and 0003 — their
  name, columns and partial predicate — before it stamps a schema, so a plain index that
  only borrows a guard name no longer passes
- Migration 0012 created `alert_deliveries` without the `is_test` column the model
  declares, so a migrated database failed every test send; revision 0013 adds it
- Revision 0014 keeps one open `no_run` alert per pipeline and removes the duplicates a
  running system had queued
- A webhook channel URL that points at a local or private host is rejected at creation
  and re-checked before each send
- `slow_threshold_ms` rejects a value above the 32-bit range the column stores
- List queries break ties on the row id, so one page can no longer repeat or skip a row
- The delivery claim commits before the HTTP send, so a slow endpoint no longer holds an
  open transaction
- `NOTIFICATIONS_ENABLED=false` now stops both the queueing and the sending
- `seed_prod` exits with an error when the configured admin already exists with another
  role, instead of starting with no owner login
- `docker-compose.prod.yml` sets `ENVIRONMENT=production`, which turns the placeholder
  `SECRET_KEY` guard on

# Architecture Decision Records (ADRs)

## ADR-001: Inline Event Processing

**Date:** 2026-06  
**Status:** Accepted

Events are processed inline during ingestion (same request/transaction),
not deferred to Celery. The Celery worker only handles the periodic
`check_stale_pipelines` scheduled task.

**Rationale:** Keeps event-to-alert latency near-zero. The Celery
`process_run_event` task exists as an escape hatch for manual
reprocessing but is not called automatically.

# Architecture Decision Records (ADRs)

## ADR-001: Process Each Event in the Ingest Request

**Date:** 2026-06
**Status:** Accepted

The API processes each run event in the request that stores it. It does not
send the event to Celery. The Celery worker only runs the periodic
`check_stale_pipelines` task.

**Reason:** The user sees the alert for a failed run as soon as the run page
opens. No queue and no worker have to be up for that alert to exist.

The `process_run_event` Celery task still exists. An operator can start it by
hand to process a run again. No code starts it automatically.

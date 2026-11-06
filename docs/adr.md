# Architecture Decision Records (ADRs)

## ADR-001: Process Each Event in the Ingest Request

**Date:** 2026-06
**Status:** Accepted

The API processes each run event in the request that stores it. It does not
send the event to Celery. The Celery worker only runs the scheduled tasks that
`beat_schedule` starts.

**Reason:** The user sees the alert for a failed run as soon as the run page
opens. No queue and no worker have to be up for that alert to exist.

The `process_run_event` Celery task still exists. An operator can start it by
hand to process a run again. No code starts it automatically.

## ADR-002: Deliver Alerts Through a Transactional Outbox

**Date:** 2026-11
**Status:** Accepted

The API does not call a webhook inside the ingest request. It writes one row in
`alert_deliveries` for each new alert and each active channel, in the same
transaction that stores the alert. Celery Beat runs `deliver_pending_alerts`
every minute. That task reads the due rows, posts them and stores the answer.

**Reason:** An ingest request must not wait for a customer endpoint, and it must
not fail because that endpoint is down. The outbox row makes the promise to send
part of the alert transaction: an alert that is stored is always delivered
later, and a rolled back ingest leaves no delivery behind. A slow or dead
receiver costs a retry, not a lost run event.

**Consequences:**

- A notification arrives up to one minute after the alert, not immediately.
- A worker that dies mid-send leaves the row pending. The next pass sends it
  again, so a receiver can see one alert twice. Receivers should treat
  `X-Arbiter-Delivery` as an idempotency key.
- One unique row per alert and channel keeps duplicate alerts from queueing a
  second send.
- The signing secret is stored in clear text, because the API must compute the
  HMAC. It never returns the secret after creation. Use a secret dedicated to
  Arbiter.

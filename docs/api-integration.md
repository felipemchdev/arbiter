# API Integration Guide

This guide tells you how to send run data to the Arbiter API. It also tells you
what the API returns.

## Authentication

Use one method per request. The API reads the `Authorization` header first. If
that header has no bearer token, the API uses the `X-API-Key` header.

| Method | Use it for | Header |
| --- | --- | --- |
| JWT | Dashboard users | `Authorization: Bearer <token>` |
| API key | The collector, the SDK, CI/CD jobs | `X-API-Key: arb_test_xxx` |

`AUTH_MODE` can disable one of the two methods:

- `AUTH_MODE=api_keys` - the API returns 401 for every JWT.
- `AUTH_MODE=jwt` - the API returns 401 for every API key.
- `API_KEYS_ENABLED=false` - the API returns 401 for every API key.

## API key scopes

Each API key stores a comma separated list of scopes. A key with
`collector:write` can send run data. A key with `org:admin` gets the owner role,
so it can also manage pipelines, users and keys. The API checks the scope for
the route. It returns 403 when the key does not have that scope.

A new key gets `collector:write` only. Give a key more scopes only when a
client needs them.

## Status codes

| Code | The API returns it when |
| --- | --- |
| 201 | The API stored a new run |
| 401 | No credential, a bad token, a revoked key or a disabled method |
| 403 | The user has the wrong role or the key has no required scope |
| 422 | A payload field has the wrong type or an unknown value |
| 429 | The caller passed the rate limit for that route |

## Endpoints

| Method | Path | Who can call it | What the API returns |
| --- | --- | --- | --- |
| POST | /api/v1/auth/token | A user with a correct password | An access token and a refresh token |
| POST | /api/v1/auth/refresh | A valid refresh token | A new token pair |
| GET | /api/v1/health | Anyone | The API status and its dependencies |
| GET | /api/v1/metrics | Any valid credential | Run counts for today |
| GET | /api/v1/metrics/runs-per-day | Any valid credential | The run count for each of the last 7 days |
| GET | /api/v1/pipelines | Any valid credential | One page of pipelines, with optional filters |
| POST | /api/v1/pipelines | An owner | The new pipeline |
| GET | /api/v1/pipelines/:id | Any valid credential | One pipeline with its DAG |
| PATCH | /api/v1/pipelines/:id | An owner | The pipeline with the new budget |
| GET | /api/v1/pipelines/:id/runs | Any valid credential | One page of runs |
| DELETE | /api/v1/pipelines/:id | An owner | Nothing (204) |
| POST | /api/v1/runs | A key with `collector:write` | The stored run (201) |
| POST | /api/v1/runs/ingest | A key with `collector:write` | The number of stored runs |
| GET | /api/v1/runs | Any valid credential | One page of runs from every pipeline, with optional filters |
| GET | /api/v1/runs/:id | Any valid credential | One run |
| GET | /api/v1/runs/:id/tasks | Any valid credential | The task instances of that run |
| GET | /api/v1/alerts | Any valid credential | One page of open alerts, or resolved alerts on request |
| PUT | /api/v1/alerts/:id/resolve | An owner | The resolved alert |
| GET | /api/v1/api-keys | An owner | The keys of the organisation |
| POST | /api/v1/api-keys | An owner | The new key, shown one time only |
| POST | /api/v1/api-keys/:id/revoke | An owner | A confirmation message |
| DELETE | /api/v1/api-keys/:id | An owner | A confirmation message |
| GET | /api/v1/notification-channels | Any valid credential | The webhook channels, with the last delivery of each |
| POST | /api/v1/notification-channels | An owner | The new channel and its signing secret, shown one time only |
| PATCH | /api/v1/notification-channels/:id | An owner | The channel with the changed fields |
| POST | /api/v1/notification-channels/:id/test | An owner | The result of one sample send |
| DELETE | /api/v1/notification-channels/:id | An owner | A confirmation message |
| GET | /api/v1/notification-channels/deliveries | Any valid credential | One page of delivery attempts, with optional filters |

## Procedure: Filter a list

Every list endpoint takes `limit` and `offset`. Four endpoints take more filters.

| Endpoint | Extra filters |
| --- | --- |
| `GET /api/v1/runs` | `status`, `pipeline_id`, `started_from`, `started_to`, `q` |
| `GET /api/v1/pipelines` | `status`, `q` |
| `GET /api/v1/alerts` | `type`, `resolved`, `pipeline_id` |
| `GET /api/v1/notification-channels/deliveries` | `status`, `channel_id` |

| Filter | Result |
| --- | --- |
| `status` | Runs with that status, pipelines whose last run had that status, or deliveries in that state |
| `pipeline_id` | Only the rows of one pipeline |
| `channel_id` | Only the deliveries of one channel |
| `type` | Only the alerts of one alert type |
| `resolved` | Open alerts with `false`, resolved alerts with `true`. The default keeps open alerts. |
| `q` | Rows whose run id or error text contains the search term. The match ignores letter case. |
| `started_from`, `started_to` | Runs that started inside the window. Both bounds are inclusive. |

1. Put the filters in the query string.
2. Leave out a filter when you want every value. Do not send `status=` with an
   empty value. The API answers 422 for that request.
3. Read `total` in the page envelope. `total` counts the filtered rows, not the
   whole table.
4. Percent-encode a date filter. A `+` in `2026-11-01T00:00:00+00:00` must be
   `%2B`. The `Z` form, `2026-11-01T00:00:00Z`, needs no encoding.

Each row of `GET /api/v1/runs` also carries `pipeline_id` and `pipeline_name`.
You do not need a second call to label the row.

```sh
curl "http://localhost:8000/api/v1/runs?status=failed&q=timeout&limit=20" \
  -H "Authorization: Bearer <access-token>"
```

## Rate limits

The API limits writes per client address and per route:

- `POST /api/v1/runs` - 120 requests in one minute.
- `POST /api/v1/runs/ingest` - 30 requests in one minute.

If you get 429, wait, then send the data again. Use the batch route when you
have many runs. One batch request counts as one request.

## Procedure: Send one run

1. Open the API Keys page in the dashboard.
2. Create a key with the `collector:write` scope. Copy the key. The dashboard
   shows the key only once.
3. Put that key in the `X-API-Key` header.
4. Run the command below. The API stores the run and returns the count.

```sh
curl -X POST http://localhost:8000/api/v1/runs/ingest \
  -H "X-API-Key: arb_test_xxx" \
  -H "Content-Type: application/json" \
  -d '{"dags":[{"dag_id":"demo","name":"demo_pipeline","runs":[{...}]}]}'
```

Every run needs `started_at`. The API computes `duration_ms` when the run also
has `finished_at`. If a run has the same `run_id` as a stored run of that
pipeline, the API updates the stored run. It does not create a second run.

See the root README for a complete payload example.

## Procedure: Set a duration budget

1. Sign in to the dashboard as an owner.
2. Open the pipeline page. The Duration budget card holds the budget in
   milliseconds.
3. Enter a value and select Save. The API stores the value on the pipeline.

Use the API when you do not want the dashboard:

```sh
curl -X PATCH http://localhost:8000/api/v1/pipelines/<pipeline-id> \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"slow_threshold_ms": 60000}'
```

The value must be a whole number above zero. The API answers 422 for `0`, for a
negative value, and for a value that is not a number.

Send `"slow_threshold_ms": null` to remove the budget. The API then compares
each run with the 95th percentile of the last successful runs of the same
pipeline. It creates no alert while that history stays short.

## Procedure: Register a webhook channel

A channel is one HTTPS endpoint that receives alert notifications. One
organisation can register ten channels.

1. Open the Notifications page in the dashboard as an owner.
2. Select **New channel**, enter a name and the endpoint URL, then select
   **Create channel**.
3. Copy the signing secret. The API shows it once. Store it in your receiver.
4. Select **Test** on the new row. The API sends one sample payload now and
   shows the answer.

Use the API when you do not want the dashboard:

```sh
curl -X POST http://localhost:8000/api/v1/notification-channels \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "on-call", "url": "https://example.com/arbiter/hooks", "enabled": true}'
```

The URL must start with `http://` or `https://`. The API answers 422 for any
other scheme.

## Alert notification payload

The worker sends one `POST` per alert and per channel. The body is JSON:

```json
{
  "delivery_id": "0f3c…",
  "attempt": 1,
  "sent_at": "2026-11-05T12:00:00+00:00",
  "alert": {
    "id": "9b2d…",
    "type": "failure",
    "message": "Run nightly-1 failed",
    "resolved": false,
    "created_at": "2026-11-05T11:59:58+00:00"
  },
  "pipeline": { "id": "4a71…", "name": "nightly_etl" },
  "run": {
    "id": "7742…",
    "run_id": "nightly-1",
    "status": "failed",
    "started_at": "2026-11-05T11:00:00+00:00",
    "finished_at": "2026-11-05T11:59:58+00:00",
    "duration_ms": 3598000,
    "error_message": "row count mismatch"
  }
}
```

`run` is `null` for a `no_run` alert. No run exists for that alert.

These headers accompany the body:

| Header | Value |
| --- | --- |
| `X-Arbiter-Signature` | `sha256=<hmac>` of the raw request body |
| `X-Arbiter-Delivery` | The `delivery_id` of this row |
| `X-Arbiter-Attempt` | The attempt number, starting at 1 |
| `User-Agent` | `arbiter-webhook/0.1` |

Verify the signature with the channel secret before you trust the body:

```python
import hashlib, hmac

expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
if received_signature != "sha256=" + expected:
    abort(400)
```

Hash the bytes you received. Do not re-encode the parsed JSON: a different key
order or spacing gives a different digest.

## Delivery states

Each alert and channel pair creates one delivery row:

| State | Meaning |
| --- | --- |
| `pending` | The worker has not delivered the alert yet. It retries with an exponential backoff. |
| `delivered` | The endpoint answered `2xx`. |
| `failed` | The endpoint never answered `2xx`, or the channel was removed. The worker stops. |

The worker sends every due delivery once per minute. Set
`NOTIFICATION_MAX_ATTEMPTS` and `NOTIFICATION_BACKOFF_SECONDS` to change that
policy. A channel that you mute receives no new delivery rows. A duplicate
alert creates no second delivery.

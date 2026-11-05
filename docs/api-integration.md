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

## Procedure: Filter a list

Every list endpoint takes `limit` and `offset`. Three endpoints take more filters.

| Endpoint | Extra filters |
| --- | --- |
| `GET /api/v1/runs` | `status`, `pipeline_id`, `started_from`, `started_to`, `q` |
| `GET /api/v1/pipelines` | `status`, `q` |
| `GET /api/v1/alerts` | `type`, `resolved`, `pipeline_id` |

| Filter | Result |
| --- | --- |
| `status` | Runs with that status, or pipelines whose last run had that status |
| `pipeline_id` | Only the rows of one pipeline |
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

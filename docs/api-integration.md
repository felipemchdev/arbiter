# API Integration Guide

## Authentication

Two methods, mutually exclusive per request:

1. **JWT** (dashboard users): `Authorization: Bearer <token>`
2. **API Key** (SDK/collector): `X-API-Key: arb_xxx`

## Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | /api/v1/auth/token | None | Login, returns JWT |
| GET | /api/v1/health | None | Health check |
| GET | /api/v1/metrics | JWT | Today's run stats |
| GET | /api/v1/metrics/runs-per-day | JWT | 7-day time series |
| GET | /api/v1/pipelines | JWT | List pipelines |
| POST | /api/v1/runs | API Key | Ingest single run |
| POST | /api/v1/runs/ingest | API Key | Ingest batch (DAGs + runs) |
| GET | /api/v1/runs/:id | JWT | Run detail |
| GET | /api/v1/runs/:id/tasks | JWT | Task instances |
| GET | /api/v1/alerts | JWT | Active alerts |
| PUT | /api/v1/alerts/:id/resolve | JWT (owner) | Resolve alert |

## Example: Ingest a Run

```sh
curl -X POST http://localhost:8000/api/v1/runs/ingest \
  -H "X-API-Key: arb_xxx" \
  -H "Content-Type: application/json" \
  -d '{"dags":[{...}]}'
```

See the root README for a complete curl example.

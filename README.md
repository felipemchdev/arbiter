# Arbiter

Pipeline observability — push events, get a dashboard.

Arbiter is a lightweight observability layer for data pipelines. It does not orchestrate, schedule, or execute anything. It receives run events via HTTP and displays DAGs, metrics, task timelines, and alerts.

## Architecture

```
                   POST /api/v1/runs/ingest
                   POST /api/v1/runs/ingest
┌──────────────┐  ──────────────────────────────►  ┌──────────────┐
│  Airflow     │                                    │              │
│  Azure Func  │                                    │  arbiter-api │
│  Python SDK  │                                    │  FastAPI     │
│  Cron Job    │                                    │  :8000       │
└──────────────┘                                    └──────┬───────┘
                                                          │
                          ┌───────────────────────────────┼───────────────────────────────┐
                          │                               │                               │
                          ▼                               ▼                               ▼
                   ┌──────────────┐              ┌──────────────┐              ┌──────────────────┐
                   │  PostgreSQL  │              │    Redis     │              │  Celery Worker   │
                   │  pipelines   │              │  broker +    │              │  + Beat          │
                   │  runs        │              │  result      │              │  check_stale     │
                   │  tasks       │              │  backend     │              │  every 10 min    │
                   │  alerts      │              └──────────────┘              └──────────────────┘
                   └──────┬───────┘
                          │
                          │  GET /api/v1/*
                          ▼
                   ┌──────────────────┐
                   │  arbiter-        │
                   │  dashboard       │
                   │  Next.js :3000   │
                   └──────────────────┘
```

### Componentes

| Serviço | Porta | Descrição |
|---|---|---|
| `arbiter-api` | 8000 | Core REST API — ingestão de runs, métricas, autenticação JWT + API keys |
| `arbiter-dashboard` | 3000 | Frontend Next.js — DAG interativo (ReactFlow), métricas, timeline, alertas, dark/light theme |
| `arbiter-worker` | — | Celery worker + beat — executa `check_stale_pipelines` a cada 10 min (alerta pipelines sem runs em 24h) |
| `arbiter-redis` | 6379 | Redis 7 — broker e result backend do Celery |
| `postgres` | 5432 | PostgreSQL 15 — único source of truth |

### Fluxo de dados

1. Um sistema externo (Airflow DAG, Azure Function, script Python, cron job) faz `POST` para a API com dados da run
2. A API persiste pipeline, run, tasks, e DAG definition no PostgreSQL em uma transação atômica
3. No mesmo request, a API processa o evento inline: calcula `duration_ms`, atualiza `last_run_status`, cria alerta de `failure` se necessário
4. O dashboard consulta a API e renderiza tudo em tempo real
5. A cada 10 minutos, o Celery Beat dispara `check_stale_pipelines` — varre pipelines sem runs em 24h e cria alertas `no_run`

## Quick Start

```sh
# 1. Clone
git clone https://github.com/felipemchdev/arbiter.git
cd arbiter

# 2. Configure
cp .env.example .env

# 3. Start
docker compose up -d

# 4. Access
# Dashboard:  http://localhost:3000  (login: admin@arbiter / arbiter26@)
# API Docs:   http://localhost:8000/docs
# API Health: http://localhost:8000/api/v1/health
```

## Ingesting a Run

```sh
# Get API key from the seed output or check the API logs
curl -X POST http://localhost:8000/api/v1/runs/ingest \
  -H "X-API-Key: arb_xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "dags": [{
      "dag_id": "demo",
      "name": "demo_pipeline",
      "runs": [{
        "run_id": "manual__2026-01-01",
        "status": "success",
        "started_at": "2026-01-01T00:00:00Z",
        "finished_at": "2026-01-01T00:05:00Z",
        "duration_ms": 300000
      }],
      "nodes": [
        {"id": "extract", "label": "Extract"},
        {"id": "transform", "label": "Transform"},
        {"id": "load", "label": "Load"}
      ],
      "edges": [
        {"source": "extract", "target": "transform"},
        {"source": "transform", "target": "load"}
      ]
    }]
  }'
```

## Credenciais Padrão

As seeds de bootstrap criam automaticamente:

| Usuário | Senha | Role |
|---|---|---|
| `admin@arbiter` | `arbiter26@` | owner |
| `viewer@arbiter` | `admin123` | viewer |

API Key aparece no log do container: `docker compose logs api | grep "API Key"`

## Development

```sh
# API
cd arbiter-api
pip install -r requirements.txt
uvicorn app.main:app --reload

# Dashboard
cd arbiter-dashboard
npm install
npm run dev

# Worker
cd arbiter-api
celery -A app.workers.celery_app worker --loglevel=info
```

## License

MIT © 2026 Felipe Machado

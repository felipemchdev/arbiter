# Arbiter

[![CI](https://github.com/felipemchdev/arbiter/actions/workflows/deploy.yml/badge.svg)](https://github.com/felipemchdev/arbiter/actions/workflows/deploy.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)


[Português](#pt-br) · [English](#en)


---

## PT-BR

### Arquitetura

```
                   POST /api/v1/runs/ingest
┌──────────────┐  ──────────────────────────────►  ┌──────────────┐
│  Airflow     │                                    │              │
│  Azure Func  │                                    │  arbiter-api │
│  Python      │                                    │  FastAPI     │
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
                   │  tasks       │              │  backend     │              │  a cada 10 min   │
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

| Serviço             | Porta | Descrição                                                                                   |
| ------------------- | ----- | ------------------------------------------------------------------------------------------- |
| `arbiter-api`       | 8000  | API REST - ingestão de runs, métricas, autenticação JWT + API keys                          |
| `arbiter-dashboard` | 3000  | Frontend Next.js - DAG interativo (ReactFlow), métricas, timeline, alertas, tema dark/light |
| `arbiter-worker`    | -     | Celery worker + beat - executa `check_stale_pipelines` a cada 10 min                        |
| `arbiter-redis`     | 6379  | Redis 7 - broker e result backend do Celery                                                 |
| `postgres`          | 5432  | PostgreSQL 15 - fonte única de verdade                                                      |

### Fluxo de dados

1. Um sistema externo (Airflow, Azure Function, script Python, cron job) faz `POST` com dados da run
2. A API persiste pipeline, run, tasks e DAG no PostgreSQL em uma transação atômica
3. No mesmo request, processa o evento inline: calcula `duration_ms`, atualiza `last_run_status`, cria alerta de `failure` se necessário
4. O dashboard consulta a API e renderiza tudo em tempo real
5. A cada 10 min, o Celery Beat dispara `check_stale_pipelines` - varre pipelines sem runs em 24h e cria alertas `no_run`

### Quick Start

```sh
git clone https://github.com/felipemchdev/arbiter.git
cd arbiter
cp .env.example .env
docker compose up -d

# Dashboard:  http://localhost:3000  (login: admin@arbiter / arbiter26@)
# API Docs:   http://localhost:8000/docs
# API Health: http://localhost:8000/api/v1/health
```

### Enviando uma Run

```sh
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

### Credenciais padrão

As seeds de bootstrap criam automaticamente:

| Usuário          | Senha        | Role   |
| ---------------- | ------------ | ------ |
| `admin@arbiter`  | `arbiter26@` | owner  |
| `viewer@arbiter` | `arbiter26@` | viewer |

API Key aparece no log: `docker compose logs api | grep "API Key"`

### Desenvolvimento

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

---

## EN

Arbiter is a lightweight observability layer for data pipelines. It does **not** orchestrate, schedule, or execute anything. It receives run events via HTTP and displays DAGs, metrics, task timelines, and alerts.

### Architecture

```
                   POST /api/v1/runs/ingest
┌──────────────┐  ──────────────────────────────►  ┌──────────────┐
│  Airflow     │                                    │              │
│  Azure Func  │                                    │  arbiter-api │
│  Python      │                                    │  FastAPI     │
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

### Components

| Service             | Port | Description                                                                                 |
| ------------------- | ---- | ------------------------------------------------------------------------------------------- |
| `arbiter-api`       | 8000 | Core REST API - run ingestion, metrics, JWT + API key auth                                  |
| `arbiter-dashboard` | 3000 | Next.js frontend - interactive DAG (ReactFlow), metrics, timeline, alerts, dark/light theme |
| `arbiter-worker`    | -    | Celery worker + beat - runs `check_stale_pipelines` every 10 min                            |
| `arbiter-redis`     | 6379 | Redis 7 - Celery broker and result backend                                                  |
| `postgres`          | 5432 | PostgreSQL 15 - single source of truth                                                      |

### Data flow

1. An external system (Airflow DAG, Azure Function, Python script, cron job) POSTs run data to the API
2. The API persists pipeline, run, tasks, and DAG definition in PostgreSQL in a single atomic transaction
3. In the same request, it processes the event inline: computes `duration_ms`, updates `last_run_status`, creates a `failure` alert if needed
4. The dashboard queries the API and renders everything in real time
5. Every 10 min, Celery Beat triggers `check_stale_pipelines` - scans for pipelines with no runs in 24h and creates `no_run` alerts

### Quick Start

```sh
git clone https://github.com/felipemchdev/arbiter.git
cd arbiter
cp .env.example .env
docker compose up -d

# Dashboard:  http://localhost:3000  (login: admin@arbiter / arbiter26@)
# API Docs:   http://localhost:8000/docs
# API Health: http://localhost:8000/api/v1/health
```

### Ingesting a Run

```sh
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

### Default Credentials

Bootstrap seeds create automatically:

| User             | Password     | Role   |
| ---------------- | ------------ | ------ |
| `admin@arbiter`  | `arbiter26@` | owner  |
| `viewer@arbiter` | `arbiter26@` | viewer |

API Key shows in container logs: `docker compose logs api | grep "API Key"`

### Development

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

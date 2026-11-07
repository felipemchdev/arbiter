# Arbiter

[![CI](https://github.com/felipemchdev/arbiter/actions/workflows/ci.yml/badge.svg)](https://github.com/felipemchdev/arbiter/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)


[Português](#pt-br) · [English](#en)

---

## PT-BR

### Arquitetura

```
                   POST /api/v1/runs/ingest
┌──────────────┐  ──────────────────────────────►  ┌──────────────┐
│  Airflow     │                                   │              │
│  Azure Func  │                                   │  arbiter-api │
│  Python      │                                   │  FastAPI     │
│  Cron Job    │                                   │  :8000       │
└──────────────┘                                   └──────┬───────┘
                                                          │
                          ┌───────────────────────────────┼───────────────────────────────┐
                          │                               │                               │
                          ▼                               ▼                               ▼
                   ┌──────────────┐              ┌──────────────┐              ┌──────────────────┐
                   │  SQLite /    │              │    Redis     │              │  Celery Worker   │
                   │  PostgreSQL  │              │  broker +    │              │  + Beat          │
                   │  pipelines   │              │  result      │              │  check_stale     │
                   │  runs        │              │  backend     │              │  a cada 10 min   │
                   │  tasks       │              └──────────────┘              └──────────────────┘
                   │  alerts      │
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

| Servico             | Porta | Funcao                                                                       |
| ------------------- | ----- | -------------------------------------------------------------------------------- |
| `arbiter-api`       | 8000  | API REST. Guarda runs, valida usuarios e entrega metricas.                  |
| `arbiter-dashboard` | 3000  | Interface Next.js. Mostra o DAG (ReactFlow), metricas, timeline, navegador de runs e alertas.  |
| `arbiter-worker`    | -     | Worker e Beat do Celery. Executa `check_stale_pipelines` a cada 10 minutos.  |
| `arbiter-redis`     | 6379  | Redis 7. Guarda a fila do Celery e o resultado das tasks.                   |
| `postgres`          | 5432  | PostgreSQL 15. Guarda pipelines, runs, tasks e alertas.                      |

Use a porta 5432 somente quando o Docker executa o PostgreSQL. Uma execucao
local sem Docker usa SQLite.

### Fluxo de dados

1. Um sistema externo envia os dados da run para a API. Esse sistema pode ser
   o Airflow, uma Azure Function, um script Python ou um cron job.
2. A API salva o pipeline, a run, as tasks e o DAG em uma unica transacao. Se
   uma escrita falha, a API nao salva nada.
3. No mesmo request, a API define `duration_ms` e `last_run_status`.
4. A API cria um alerta `failure` quando o status daquela run e `failed`.
5. A API compara `duration_ms` com o orcamento do pipeline e cria um alerta
   `duration_exceeded` quando a run passa dele. O orcamento e
   `slow_threshold_ms`, quando o dono o define. Sem ele, a API usa o p95 das
   ultimas runs de sucesso do mesmo pipeline.
6. O dashboard le os dados na API. A run nova aparece assim que a API a salva.
7. O Celery Beat executa `check_stale_pipelines` a cada 10 minutos. Essa task
   cria um alerta `no_run` para cada pipeline sem run ha 24 horas.

### Quick Start

```sh
git clone https://github.com/felipemchdev/arbiter.git
cd arbiter
cp .env.example .env
docker compose up -d
```

<!-- coderabbit-ai-generated:v1 -->

<!-- coderabbit-ai-generated-section:v1:a41124f8416bb31578b4692949546e2493c7eca93bcbb059dd6905917b3afba9 -->

Abra o `.env` antes de subir e troque cada valor `CHANGE_ME`. Use a mesma senha
em `POSTGRES_PASSWORD` e dentro de `DATABASE_URL`. Os containers nao sobem sem
`POSTGRES_PASSWORD`. Se a senha contiver caracteres especiais de URL, aplique
URL-encoding somente ao valor da senha dentro de `DATABASE_URL`. Mantenha a
senha original sem alteracoes em `POSTGRES_PASSWORD`.

<!-- /coderabbit-ai-generated:v1 -->
- Dashboard: http://localhost:3000
- Documentacao da API: http://localhost:8000/docs
- Health endpoint: http://localhost:8000/api/v1/health

O repositorio nao tem senha padrao. A seed de desenvolvimento imprime a senha de
login uma vez. Veja Credenciais padrao abaixo.

### Autenticacao

Use um metodo por request. A API primeiro le o bearer token. Se nao houver
bearer token, a API usa o header `X-API-Key`.

| Metodo      | Use para | Como funciona |
| ----------- | -------- | ------------- |
| **JWT**     | Usuarios do dashboard | O usuario faz login. A API devolve um access token valido por 15 minutos e um refresh token. |
| **API Key** | Coletor, SDK, jobs de CI/CD | O cliente envia a key no header `X-API-Key`. |

O refresh token tem duas partes: o id do token e o token. A API usa o id para
achar a linha salva, entao nao faz varredura na tabela.

O dashboard renova o access token sozinho. Quando o usuario faz logout, a API
revoga todos os refresh tokens daquele usuario.

Crie e revogue API Keys no dashboard (`/dashboard/api-keys`) ou em
`POST /api/v1/api-keys`. Uma key criada em producao comeca com `arb_live_`. Em
qualquer outro ambiente, ela comeca com `arb_test_`.

### Credenciais padrao

O repositorio nao tem senha padrao. No boot, `seed_dev.py` cria uma senha
aleatoria por usuario e a imprime uma unica vez:

```sh
docker compose logs api | grep "User created"
```

A seed de desenvolvimento tambem cria uma API key e a imprime:

```sh
docker compose logs api | grep "API Key"
```

Para usar as suas senhas, defina `ARBITER_ADMIN_USER`, `ARBITER_ADMIN_PASSWORD`,
`ARBITER_VIEWER_USER` e `ARBITER_VIEWER_PASSWORD` no `.env` antes do primeiro
boot. Quando voce define a senha, a seed nao a imprime.

### Procedimento: envie uma run

```sh
curl -X POST http://localhost:8000/api/v1/runs/ingest \
  -H "X-API-Key: arb_live_xxx" \
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

### Desenvolvimento

Execute cada bloco em um terminal separado.

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

A API precisa de um `DATABASE_URL`. Uma execucao local sem Docker usa SQLite. O
worker tambem precisa de um Redis ativo, porque o Celery pega as tasks no Redis.

Um banco SQLite criado por um seed antigo ja existe, entao o `create_all` nao
adiciona a coluna nova `slow_threshold_ms`. Faca um backup do arquivo antes de
troca-lo. Ele guarda suas pipelines, runs, alertas e usuarios. Copie o arquivo,
apague o original e rode o seed de novo, ou siga a mensagem de
`app.scripts.adopt_baseline`.

### Documentacao

- `docs/architecture.md` - os componentes e o fluxo de dados.
- `docs/api-integration.md` - como enviar runs e ler alertas pela API.
- `docs/adr.md` - as decisoes de arquitetura e os motivos delas.
- `docs/roadmap.md` - o que o Arbiter faz hoje e qual e o proximo trabalho.

---

## EN

Arbiter is an observability tool for data pipelines. Arbiter does not
orchestrate, schedule or run your jobs. Another system runs them.

You send Arbiter one event per pipeline run. You send that event over HTTP,
with the SDK or with the collector. Arbiter stores the run and shows the DAG,
the metrics, the task timeline and the alerts in a dashboard.

### Architecture

```
                   POST /api/v1/runs/ingest
┌──────────────┐  ──────────────────────────────►  ┌──────────────┐
│  Airflow     │                                   │              │
│  Azure Func  │                                   │  arbiter-api │
│  Python      │                                   │  FastAPI     │
│  Cron Job    │                                   │  :8000       │
└──────────────┘                                   └──────┬───────┘
                                                          │
                          ┌───────────────────────────────┼───────────────────────────────┐
                          │                               │                               │
                          ▼                               ▼                               ▼
                   ┌──────────────┐              ┌──────────────┐              ┌──────────────────┐
                   │  SQLite /    │              │    Redis     │              │  Celery Worker   │
                   │  PostgreSQL  │              │  broker +    │              │  + Beat          │
                   │  pipelines   │              │  result      │              │  check_stale     │
                   │  runs        │              │  backend     │              │  every 10 min    │
                   │  tasks       │              └──────────────┘              └──────────────────┘
                   │  alerts      │
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

| Service             | Port | Function                                                                              |
| ------------------- | ---- | --------------------------------------------------------------------------------------- |
| `arbiter-api`       | 8000 | REST API. It stores runs, checks users and serves metrics.                       |
| `arbiter-dashboard` | 3000 | Next.js UI. It shows the DAG (ReactFlow), metrics, timelines, the run browser and alerts.          |
| `arbiter-worker`    | -    | Celery worker and Beat. It runs `check_stale_pipelines` every 10 minutes.         |
| `arbiter-redis`     | 6379 | Redis 7. It holds the Celery queue and the task results.                          |
| `postgres`          | 5432 | PostgreSQL 15. It stores pipelines, runs, tasks and alerts.                        |

Use port 5432 only when Docker runs PostgreSQL. A local run without Docker uses
SQLite.

### Data flow

1. An external system sends run data to the API. That system can be Airflow, an
   Azure Function, a Python script or a cron job.
2. The API saves the pipeline, the run, the tasks and the DAG in one
   transaction. If one write fails, the API saves nothing.
3. In the same request, the API sets `duration_ms` and `last_run_status`.
4. The API creates a `failure` alert when the status of that run is `failed`.
5. The API compares `duration_ms` with the budget of the pipeline and creates a
   `duration_exceeded` alert when the run is longer. The budget is
   `slow_threshold_ms` when an owner sets it. Without that value the API uses
   the p95 of the last successful runs of the same pipeline.
6. The dashboard reads the data from the API. The new run appears as soon as
   the API saves it.
7. Celery Beat runs `check_stale_pipelines` every 10 minutes. That task creates
   a `no_run` alert for each pipeline with no run in 24 hours.

### Quick Start

```sh
git clone https://github.com/felipemchdev/arbiter.git
cd arbiter
cp .env.example .env
docker compose up -d
```

<!-- coderabbit-ai-generated:v1 -->

<!-- coderabbit-ai-generated-section:v1:cea3fc023849a16c62d45f44a46b1112a7dbc9c2fbeaec950064ea67e96de480 -->

Open `.env` before you start the containers and replace every `CHANGE_ME`
value. Use one password in `POSTGRES_PASSWORD` and in `DATABASE_URL`. The
containers do not start without `POSTGRES_PASSWORD`. If the password contains
URL-sensitive characters, URL-encode only the password value embedded in
`DATABASE_URL`. Keep the original password unchanged in `POSTGRES_PASSWORD`.

<!-- /coderabbit-ai-generated:v1 -->
- Dashboard: http://localhost:3000
- API docs: http://localhost:8000/docs
- Health endpoint: http://localhost:8000/api/v1/health

The repository has no default password. The dev seed prints the login password
once. See Default Credentials below.

### Authentication

Use one method per request. The API checks the bearer token first. If no bearer
token is present, the API uses the `X-API-Key` header.

| Method      | Use it for | How it works |
| ----------- | ---------- | ------------ |
| **JWT**     | Dashboard users | The user logs in. The API returns an access token that lasts 15 minutes and a refresh token. |
| **API Key** | The collector, the SDK, CI/CD jobs | The client sends the key in the `X-API-Key` header. |

A refresh token has two parts: the token id and the token itself. The API uses
the token id to find the stored row, so it does not scan the table.

The dashboard gets a new access token by itself. When a user logs out, the API
revokes every refresh token of that user.

Create and revoke API keys in the dashboard (`/dashboard/api-keys`) or with
`POST /api/v1/api-keys`. A key made in production starts with `arb_live_`. A key
made in any other environment starts with `arb_test_`.

### Default Credentials

The repository has no default password. On boot, `seed_dev.py` makes one random
password per user and prints it once:

```sh
docker compose logs api | grep "User created"
```

The dev seed also makes an API key and prints it:

```sh
docker compose logs api | grep "API Key"
```

To use your own passwords, set `ARBITER_ADMIN_USER`, `ARBITER_ADMIN_PASSWORD`,
`ARBITER_VIEWER_USER` and `ARBITER_VIEWER_PASSWORD` in `.env` before the first
boot. When you set a password, the seed does not print it.

### Procedure: Send a run

```sh
curl -X POST http://localhost:8000/api/v1/runs/ingest \
  -H "X-API-Key: arb_live_xxx" \
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

### Development

Run each block in its own terminal.

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

The API needs a `DATABASE_URL`. A local run without Docker uses SQLite. The
worker also needs a running Redis, because Celery takes its tasks from Redis.

A SQLite file that an older seed created already has the `pipelines` table, so
`create_all` does not add the new `slow_threshold_ms` column. Back the file up
before you replace it. It holds your pipelines, runs, alerts and users. Copy
the file, delete the original, then run the seed again, or follow the message
from `app.scripts.adopt_baseline`.

### Documentation

- `docs/architecture.md` - the components and the data flow.
- `docs/api-integration.md` - how to send runs and how to read alerts.
- `docs/adr.md` - the architecture decisions and their reasons.
- `docs/roadmap.md` - what Arbiter does today and what work comes next.

## License

MIT © 2026 Felipe Machado

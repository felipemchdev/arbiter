# Arbiter

Monorepo da plataforma Arbiter para observabilidade de pipelines de dados.

## Serviços

- `arbiter-api`: FastAPI + SQLAlchemy async + Celery
- `arbiter-dashboard`: Next.js 14 + Tailwind
- `arbiter-sdk`: cliente Python publicável
- `arbiter-collector`: agente de polling do Airflow

## Começando

1. Copie `.env.example` para `.env`
2. Rode `docker compose up -d`
3. Acesse `http://localhost:8000/api/v1/health`
4. Acesse `http://localhost:3000`

## Observações

- O backend usa PostgreSQL e Redis via Docker Compose.
- O dashboard sobe com login em `/login`.
- Os pacotes Python podem ser instalados separadamente quando você quiser publicar ou testar localmente.

#!/bin/sh
set -e

if [ "${RUN_SEEDS:-false}" = "true" ]; then
  echo "[bootstrap] Running OSS seeds..."
  python -m app.scripts.seed_dev
  python -m app.scripts.seed_helios
else
  echo "[bootstrap] Skipping OSS seeds (RUN_SEEDS not set)"
fi

if [ -n "${ARBITER_ADMIN_USER}" ] && [ -n "${ARBITER_ADMIN_PASSWORD}" ]; then
  echo "[bootstrap] Running production user upsert..."
  #python -m app.scripts.seed_prod
else
  echo "[bootstrap] Skipping production user upsert (env vars not set)"
fi

echo "[bootstrap] Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

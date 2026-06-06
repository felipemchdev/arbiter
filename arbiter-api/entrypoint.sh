#!/bin/sh
set -e
if [ "${RUN_SEEDS:-false}" = "true" ]; then
  echo "[bootstrap] Running seeds..."
  python -m app.scripts.seed_dev
  python -m app.scripts.seed_helios
else
  echo "[bootstrap] Skipping seeds (RUN_SEEDS not set to true)"
fi
echo "[bootstrap] Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

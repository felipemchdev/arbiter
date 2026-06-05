#!/bin/sh
set -e
echo "[bootstrap] Running seeds..."
python -m app.scripts.seed_dev
python -m app.scripts.seed_helios
echo "[bootstrap] Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
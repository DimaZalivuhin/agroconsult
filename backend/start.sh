#!/usr/bin/env bash
set -euo pipefail

echo "[start.sh] Running migrations..."
alembic upgrade head
echo "[start.sh] Migrations done. Starting gunicorn on port ${PORT:-8000}..."

exec gunicorn app.main:app \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind "0.0.0.0:${PORT:-8000}" \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info

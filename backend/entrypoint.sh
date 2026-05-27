#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."
until python -c "import socket; s=socket.socket(); s.settimeout(3); s.connect(('postgres',5432)); s.close(); print('connected')" 2>/dev/null; do
    echo "PostgreSQL is not ready yet. Retrying in 2 seconds..."
    sleep 2
done
echo "PostgreSQL is ready."

echo "Running database migrations..."
alembic upgrade head || echo "Warning: Alembic migrations skipped (no migrations found or alembic not configured yet)"

echo "Starting uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."
while ! python -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.connect(('postgres', 5432))
    s.close()
    exit(0)
except:
    exit(1)
" 2>/dev/null; do
    echo "PostgreSQL is not ready yet. Retrying in 2 seconds..."
    sleep 2
done
echo "PostgreSQL is ready."

echo "Running database migrations..."
alembic upgrade head || echo "Warning: Alembic migrations skipped (no migrations found or alembic not configured yet)"

echo "Starting uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

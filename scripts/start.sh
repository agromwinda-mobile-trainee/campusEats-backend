#!/usr/bin/env bash

set -euo pipefail

echo "[start] Appliquer migrations Django..."
python manage.py migrate --noinput

echo "[start] Collecter les fichiers statiques..."
python manage.py collectstatic --noinput --clear

WORKERS="${GUNICORN_WORKERS:-3}"
echo "[start] Démarrer Gunicorn (${WORKERS} workers)..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers "${WORKERS}" --timeout 60


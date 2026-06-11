#!/bin/bash
set -e

export DJANGO_ENV="${DJANGO_ENV:-production}"
export PORT="${PORT:-8000}"

python manage.py collectstatic --noinput

exec gunicorn aho_datacapturetool.wsgi:application \
  --bind "0.0.0.0:${PORT}" \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout "${GUNICORN_TIMEOUT:-600}"

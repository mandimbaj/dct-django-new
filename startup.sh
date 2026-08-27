#!/bin/bash
set -e

export DJANGO_ENV="${DJANGO_ENV:-production}"
export PORT="${PORT:-8000}"

# Static collection can involve a remote Azure Blob container and must not
# block the web process during an App Service restart. Run it explicitly as a
# deployment task when needed, or opt in with RUN_COLLECTSTATIC_ON_STARTUP=true.
if [[ "${RUN_COLLECTSTATIC_ON_STARTUP:-false}" == "true" ]]; then
  python manage.py collectstatic --noinput
fi

exec gunicorn aho_datacapturetool.wsgi:application \
  --bind "0.0.0.0:${PORT}" \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout "${GUNICORN_TIMEOUT:-600}" \
  --access-logfile - \
  --error-logfile - \
  --capture-output

#!/bin/sh
set -eu
# Scaffold-only: opt in to generating migrations for the current development
# model set. Production must ship reviewed, versioned migrations and keep this off.
if [ "${YFEN_BOOTSTRAP_MIGRATIONS:-false}" = "true" ]; then
  python manage.py makemigrations identity tenancy sources actions alerts audit --noinput
fi
python manage.py migrate --noinput
exec "$@"

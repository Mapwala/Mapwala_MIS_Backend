#!/bin/sh

USE_DOCKER_DB="${USE_DOCKER_DB:-false}"

if [ "$USE_DOCKER_DB" = "true" ] || [ "$USE_DOCKER_DB" = "True" ] || [ "$USE_DOCKER_DB" = "1" ]; then
  export DB_HOST="${DOCKER_PG_HOST:-db}"
  export DB_NAME="${DOCKER_DB_NAME:-${DB_NAME}}"
  export DB_USER="${DOCKER_DB_USER:-${DB_USER}}"
  export DB_PASSWORD="${DOCKER_DB_PASSWORD:-${DB_PASSWORD}}"
else
  export DB_HOST="${HOST_PG_HOST:-${DB_HOST:-host.docker.internal}}"
fi

export DB_PORT="${DB_PORT:-5432}"

echo "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."

while ! nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 1
done

echo "PostgreSQL is reachable"

python manage.py makemigrations
python manage.py migrate

exec "$@"

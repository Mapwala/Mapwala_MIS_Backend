#!/bin/sh

echo "Waiting for PostgreSQL..."

while ! nc -z db 5432; do
  sleep 1
done

echo "PostgreSQL started"

echo "Running makemigrations..."
python manage.py makemigrations

echo "Running migrate..."
python manage.py migrate

echo "Starting Django server..."
exec "$@"

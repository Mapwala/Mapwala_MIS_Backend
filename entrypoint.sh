#!/bin/sh
set -e

DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}
MAX_RETRIES=30
RETRY_COUNT=0

echo "⏳ Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."

until pg_isready -h "$DB_HOST" -p "$DB_PORT" -q; do
  RETRY_COUNT=$((RETRY_COUNT + 1))
  if [ "$RETRY_COUNT" -ge "$MAX_RETRIES" ]; then
    echo "❌ PostgreSQL did not become ready in time. Exiting."
    exit 1
  fi
  echo "  Retrying... ($RETRY_COUNT/$MAX_RETRIES)"
  sleep 2
done

echo "✅ PostgreSQL is ready"

echo "📦 Running migrations..."
python manage.py migrate --no-input

echo "📁 Collecting static files..."
python manage.py collectstatic --no-input

echo "👤 Ensuring standard user exists..."
python manage.py shell -c "
import os
from django.contrib.auth import get_user_model

User = get_user_model()

username = os.getenv('APP_USERNAME', '9876543210').strip()
password = os.getenv('APP_PASSWORD', 'Test@1234').strip()

if not username or not password:
    raise RuntimeError('APP_USERNAME and APP_PASSWORD environment variables must be set and non-empty.')

if User.objects.filter(username=username).exists():
    print('ℹ️  User already exists, skipping creation.')
else:
    User.objects.create_user(
        username=username,
        password=password,
        is_staff=True,
        is_superuser=False,
    )
    print('✅ Standard user created successfully.')
"

echo "🔑 Ensuring superuser exists..."
python manage.py shell -c "
import os
from django.contrib.auth import get_user_model

User = get_user_model()

username = os.getenv('SUPERUSER_USERNAME', 'admin').strip()
password = os.getenv('SUPERUSER_PASSWORD', 'Admin@1234').strip()
email = os.getenv('SUPERUSER_EMAIL', 'admin@admin.com').strip()

if not username or not password:
    raise RuntimeError('SUPERUSER_USERNAME and SUPERUSER_PASSWORD environment variables must be set and non-empty.')

if User.objects.filter(username=username).exists():
    print('ℹ️  Superuser already exists, skipping creation.')
else:
    User.objects.create_superuser(
        username=username,
        password=password,
        email=email,
    )
    print('✅ Superuser created successfully.')
"

exec "$@"
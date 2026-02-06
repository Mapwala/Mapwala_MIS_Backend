#!/bin/sh
set -e

echo "⏳ Waiting for PostgreSQL..."

DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}

until nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 1
done

echo "✅ PostgreSQL started"

echo "📦 Running migrations..."
python manage.py makemigrations
python manage.py migrate

echo "👤 Ensuring standard user exists..."

python manage.py shell -c "
import os
from django.contrib.auth import get_user_model

User = get_user_model()

username = os.getenv('APP_USERNAME', 'app_user')
password = os.getenv('APP_PASSWORD', 'app_password')

if not username or not password:
    raise RuntimeError('APP_USERNAME and APP_PASSWORD must be set')

if User.objects.filter(username=username).exists():
    print('ℹ️  User already exists')
else:
    User.objects.create_user(
        username=username,
        password=password,
        is_staff=True,
        is_superuser=False
    )
    print('✅ Standard user created')
"

exec "$@"

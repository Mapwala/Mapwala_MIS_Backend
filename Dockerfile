# Use official Python image
FROM python:3.12-slim

# Prevent Python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# System dependencies (for psycopg, file handling)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for Docker cache)
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy project files
COPY . /app/

# Collect static files (safe even if unused now)
RUN python manage.py collectstatic --noinput || true

# Expose Django port
EXPOSE 8000

# Start server (development-safe, production via gunicorn later)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

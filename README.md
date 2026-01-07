# Mapwala MIS Backend

This is the backend service for **Mapwala MIS**, built using **Django + Django REST Framework** with **JWT authentication**.

The system provides secure APIs for:
- User login
- State management
- District management

All APIs are protected using **JWT access tokens (24-hour validity)**.

---

## Tech Stack

- Python 3.x
- Django
- Django REST Framework
- Simple JWT (Access Token only)
- PostgreSQL
- Postman (for API testing)

---

## Project Setup

### 1️ Clone the repository
```bash
git clone <repository-url>
cd Mapwala_MIS_Backend

2️ Create & activate virtual environment
python -m venv vir_env
source vir_env/bin/activate


3️ Install dependencies
pip install -r requirements.txt


4️ Create .env file
SECRET_KEY=your_secret_key
DEBUG=True
DATABASE_URL=postgresql://user:password@localhost:5432/db_name


5️ Run migrations
python manage.py makemigrations
python manage.py migrate


6️ Create admin user
python manage.py createsuperuser


7️ Run server
python manage.py runserver


Server will start at:
http://127.0.0.1:8000/

_______________________________________________________________________________________________________________________

Authentication (Login API)

Endpoint
POST /api/auth/login/

Request (cURL)
curl --location 'http://127.0.0.1:8000/api/auth/login/' \
--header 'Content-Type: application/json' \
--data-raw '{
  "username": "test",
  "password": "Test@1234",
  "accepted_terms": true
}'

Response
{
  "message": "Login successful",
  "access_token": "<JWT_ACCESS_TOKEN>",
  "expires_in_hours": 24,
  "user": {
    "id": 2,
    "username": "test",
    "is_staff": false,
    "is_superuser": false
    }
}
_______________________________________________________________________________________________________________________

Copy the access_token
This token must be sent in all protected APIs:

Authorization: Bearer <JWT_ACCESS_TOKEN>
_______________________________________________________________________________________________________________________

State APIs


1️ Create State

curl --location 'http://127.0.0.1:8000/api/states/' \
--header 'Authorization: Bearer <ACCESS_TOKEN>' \
--header 'Content-Type: application/json' \
--data '{
  "name": "Haryana",
  "status": "active"
} '


2️ List All States

curl --location 'http://127.0.0.1:8000/api/states/' \
--header 'Authorization: Bearer <ACCESS_TOKEN>


3️ Search State

curl --location 'http://127.0.0.1:8000/api/states/?search=Raj' \
--header 'Authorization: Bearer <ACCESS_TOKEN>'

4️ Get Active States (Dropdown API)

curl --location 'http://127.0.0.1:8000/api/states/active/' \
--header 'Authorization: Bearer <ACCESS_TOKEN>'


5️ Update State

curl --location --request PUT 'http://127.0.0.1:8000/api/states/1/' \
--header 'Authorization: Bearer <ACCESS_TOKEN>' \
--header 'Content-Type: application/json' \
--data-raw '{
  "name": "New York",
  "status": "inactive"
}'


6️ Delete State (with validation)

curl --location --request DELETE 'http://127.0.0.1:8000/api/states/3/' \
--header 'Authorization: Bearer <ACCESS_TOKEN>'

    ❗ If the state has linked districts, deletion will fail:
    {
    "error": "State cannot be deleted because it has linked districts."
    }

_______________________________________________________________________________________________________________________

District APIs

1️ Create District

curl --location 'http://127.0.0.1:8000/api/districts/' \
--header 'Authorization: Bearer <ACCESS_TOKEN>' \
--header 'Content-Type: application/json' \
--data-raw '{
  "name": "Yamuna Nagar",
  "code": "YNR",
  "state": 8,
  "status": "active"
}'


2️ List All Districts

curl --location 'http://127.0.0.1:8000/api/districts/' \
--header 'Authorization: Bearer <ACCESS_TOKEN>'


3️ Filter Districts by State

curl --location 'http://127.0.0.1:8000/api/districts/?state=4' \
--header 'Authorization: Bearer <ACCESS_TOKEN>'


4️ Search Districts

curl --location 'http://127.0.0.1:8000/api/districts/?search=AMD' \
--header 'Authorization: Bearer <ACCESS_TOKEN>'


5️ Update District

curl --location --request PUT 'http://127.0.0.1:8000/api/districts/1/' \
--header 'Authorization: Bearer <ACCESS_TOKEN>' \
--header 'Content-Type: application/json' \
--data-raw '{
  "name": "Ahmedabad",
  "code": "AMD",
  "state": 4,
  "status": "inactive"
}'


6️ Delete District

curl --location --request DELETE 'http://127.0.0.1:8000/api/districts/35/' \
--header 'Authorization: Bearer <ACCESS_TOKEN>'


Security Notes:

    All APIs require JWT authentication
    Token expires after 24 hours
    No refresh token is used
    Users are created via Django Admin
    State deletion is blocked if districts exist

_______________________________________________________________________________________________________________________

Docker Setup (Recommended for Local & Deployment)
This project supports running the backend using Docker and Docker Compose, which simplifies environment setup and ensures consistency across systems.
_______________________________________________________________________________________________________________________

Prerequisites

Make sure the following are installed on your system:

    Docker
    Docker Compose v2

Verify installation:

docker --version
docker compose version
_______________________________________________________________________________________________________________________

Environment Configuration

Create a .env file in the project root (same level as docker-compose.yml):

DEBUG=True
SECRET_KEY="your-secret-key"

DATABASE_URL=postgresql://postgres:your_password@db:5432/mapwala_db

Important notes:

    db is the PostgreSQL service name from docker-compose.yml

    Do not use localhost inside Docker

    Do not add spaces around =

_______________________________________________________________________________________________________________________

Build and Run with Docker:

1️ Stop and remove any existing containers (recommended first run)

docker-compose down -v

This ensures a clean database and volume state.

_______________________________________________________________________________________________________________________

2️ Build Docker images

docker-compose build
_______________________________________________________________________________________________________________________

3️ Start containers

docker-compose up

Or run in background:

docker-compose up -d

This will start:
  Django backend container
  PostgreSQL database container

_______________________________________________________________________________________________________________________

Run Database Migrations (Required)

After containers are running, apply migrations:

docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate
_______________________________________________________________________________________________________________________

Create Admin (Superuser)

docker-compose exec backend python manage.py createsuperuser

  Use this user to log in to the Django Admin panel.
_______________________________________________________________________________________________________________________

Access the Application

Backend API:
http://127.0.0.1:8000/

Django Admin:

http://127.0.0.1:8000/admin/
_______________________________________________________________________________________________________________________

File Uploads & Media
Uploaded files (GST, PAN, TAN documents, etc.) are stored in a Docker volume:

media/

This ensures files persist even if containers restart.

_______________________________________________________________________________________________________________________

Common Docker Commands

Stop containers:
docker-compose down

Stop and remove containers + volumes:
docker-compose down -v

View running containers:
docker ps

View logs:
docker-compose logs -f

_______________________________________________________________________________________________________________________

Notes for Production

This Docker setup is intended for development and staging.
For production deployment, it is recommended to:
    Use Gunicorn instead of runserver
    Add Nginx as a reverse proxy
    Set DEBUG=False
    Restrict ALLOWED_HOSTS
    Use environment-specific secrets

Summary:
    Docker provides a consistent and repeatable setup
    No local PostgreSQL installation required
    Easy onboarding for new developers
    Suitable for deployment-ready environments

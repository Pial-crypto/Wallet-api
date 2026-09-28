# Wallet API

## Tech Stack
- Django
- Django REST Framework
- PostgreSQL
- Supabase

## Setup

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

## Environment

DATABASE_URL=...

## Run

python manage.py migrate
python manage.py runserver

## Authentication

X-Tenant-ID: <tenant-id>

or

X-API-Key: <tenant-api-key>

## Endpoints

POST /api/tenants/
POST /api/users/
POST /api/wallets/

POST /api/wallets/<id>/deposit/
POST /api/wallets/<id>/withdraw/
POST /api/wallets/<id>/transfer/

GET /api/wallets/<id>/balance/
GET /api/wallets/<id>/transactions/

## Tests

python manage.py test tests --keepdb
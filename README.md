# UniDocs Backend API

A production-oriented backend API for UniDocs, a university document and workflow platform.

## What this project demonstrates

- FastAPI application design with typed request and response schemas.
- Authentication, authorization, and role-based access control.
- PostgreSQL-ready persistence with SQLAlchemy and Alembic migrations.
- Service-layer separation for authentication, users, administration, and domain workflows.
- Automated tests with pytest.
- Docker-based local deployment.

## Technology stack

- Python 3.11+
- FastAPI and Pydantic
- SQLAlchemy and Alembic
- PostgreSQL
- Pytest
- Docker

## Project structure

```text
app/
├── api/          # HTTP routes and dependencies
├── core/         # settings, security, and shared infrastructure
├── models/       # database models
├── schemas/      # validated API contracts
└── services/     # business logic
alembic/          # database migrations
tests/            # automated tests
```

## Local setup

```bash
git clone https://github.com/albadyzaldyn111-a11y/unidocs-backend-api.git
cd unidocs-backend-api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill local development values in .env; never commit real secrets.
alembic upgrade head
uvicorn app.main:app --reload
```

Run the test suite with:

```bash
pytest -q
```

## Security note

This repository intentionally contains configuration examples only. Production credentials, tokens, database URLs, and private user data must be supplied through environment variables and must never be committed.

## Status

Active engineering project. APIs and database contracts may evolve as the UniDocs product develops.

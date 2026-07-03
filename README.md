# Clinix Backend

> The Sovereign Clinical Agent — Backend API

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116+-00a2a2.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

Clinix is an agentic clinical operating system for Nigerian teaching hospitals. This repository contains the backend API that powers:

- AI-assisted encounter documentation via MCP (Model Context Protocol)
- Patient data wallet integration with Chekk
- Verified clinical credits and portfolio generation
- Supervisor review and approval workflows
- Real-time symptom analysis and action skill orchestration

The backend is built with **FastAPI**, uses **PostgreSQL** as the primary database, **Redis** for caching and queues, and integrates with **OpenAI GPT-4** for clinical AI analysis.

---

## Tech Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Framework | FastAPI | ^0.116 |
| ORM | SQLModel | ^0.0.22 |
| Database | PostgreSQL | 15+ |
| Cache/Queue | Redis | 7+ |
| AI Engine | OpenAI + MCP | GPT-4 |
| Auth | JWT (python-jose) | ^3.3 |
| Password Hashing | bcrypt | ^4.1 |
| Validation | Pydantic | ^2.0 |
| Testing | pytest | ^8.0 |
| Deployment | Docker, Uvicorn | — |

---

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python** 3.11 or higher
- **PostgreSQL** 15 or higher
- **Redis** 7 or higher
- **Docker** & **Docker Compose** (optional, for containerized setup)
- **Git**

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/clinix-backend.git
cd clinix-backend
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Project Structure

```
clinix-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration and environment variables
│   ├── database.py             # Database connection and session management
│   ├── models/                 # SQLModel database models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── patient.py
│   │   ├── encounter.py
│   │   ├── wallet_record.py
│   │   ├── clinical_credit.py
│   │   └── action_skill_log.py
│   ├── schemas/                # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── patient.py
│   │   ├── encounter.py
│   │   ├── wallet.py
│   │   └── portfolio.py
│   ├── routers/                # API route handlers
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── patients.py
│   │   ├── encounters.py
│   │   ├── wallets.py
│   │   ├── portfolio.py
│   │   └── supervisor.py
│   ├── services/               # Business logic layer
│   │   ├── __init__.py
│   │   ├── ai_service.py       # OpenAI/MCP integration
│   │   ├── wallet_service.py   # Chekk wallet operations
│   │   ├── credit_service.py   # Clinical credit calculation
│   │   └── sms_service.py      # Twilio SMS notifications
│   ├── core/                   # Core utilities
│   │   ├── __init__.py
│   │   ├── security.py         # JWT, password hashing
│   │   ├── permissions.py      # Role-based access control
│   │   └── exceptions.py       # Custom exceptions
│   └── dependencies.py         # FastAPI dependencies (DB session, auth)
├── alembic/                    # Database migration files
│   ├── versions/
│   └── env.py
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_patients.py
│   ├── test_encounters.py
│   └── test_api.py
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── .env.example                # Example environment variables
├── .env                        # Local environment variables (gitignored)
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
├── alembic.ini
└── README.md
```

---

## Environment Variables

Create a `.env` file in the project root. See `.env.example` for reference.

```env
# Application
APP_NAME=Clinix
DEBUG=true
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql://clinix_user:clinix_pass@localhost:5432/clinix_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# Ollama AI
AI_ENGINE=ollama
OLLAMA_URL=https://api.ollama.ai
OLLAMA_MODEL=llama2
OLLAMA_API_KEY=your-ollama-api-key-here

# Chekk (Patient Data Wallets)
CHEKK_API_KEY=chk_...
CHEKK_API_URL=https://api.chekk.io/v1

# Twilio (SMS Notifications)
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+234...

# Hospital
DEFAULT_HOSPITAL=LAUTECH Teaching Hospital
```

> ⚠️ **Never commit `.env` to version control.** It is already in `.gitignore`.

---

## Database Setup

### Option A: Local PostgreSQL

1. Create the database:

```bash
psql -U postgres -c "CREATE DATABASE clinix_db;"
psql -U postgres -c "CREATE USER clinix_user WITH PASSWORD 'clinix_pass';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE clinix_db TO clinix_user;"
```

2. Run migrations:

```bash
alembic upgrade head
```

3. (Optional) Seed demo data:

```bash
python scripts/seed_data.py
```

### Option B: Docker Compose

```bash
docker-compose up -d db redis
alembic upgrade head
```

This spins up PostgreSQL and Redis containers with pre-configured credentials.

---

## Running the Application

### Development Mode (with auto-reload)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Or using Docker:

```bash
docker-compose up -d
```

The API will be available at `http://localhost:8000`.

---

## API Documentation

FastAPI auto-generates interactive API documentation:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Register new user |
| `POST` | `/api/v1/auth/login` | Authenticate and get tokens |
| `POST` | `/api/v1/auth/refresh` | Refresh access token |
| `GET` | `/api/v1/patients` | List/search patients |
| `GET` | `/api/v1/patients/queue` | Get today's patient queue |
| `POST` | `/api/v1/encounters` | Create new encounter |
| `POST` | `/api/v1/encounters/{id}/ai-analyze` | Trigger AI analysis |
| `PATCH` | `/api/v1/encounters/{id}` | Update encounter |
| `POST` | `/api/v1/encounters/{id}/finalize` | Submit for review |
| `POST` | `/api/v1/wallets/{patient_id}/push` | Push to patient wallet |
| `GET` | `/api/v1/portfolio/me` | Get student portfolio |
| `GET` | `/api/v1/supervisor/queue` | Get pending reviews |
| `POST` | `/api/v1/supervisor/encounters/{id}/approve` | Approve encounter |

---

## Testing

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
```

### Run Specific Test File

```bash
pytest tests/test_encounters.py -v
```

### Test Database

Tests use a separate PostgreSQL database (`clinix_test_db`) that is created and torn down automatically. Configure it via:

```env
TEST_DATABASE_URL=postgresql://clinix_user:clinix_pass@localhost:5432/clinix_test_db
```

---

## Deployment

### Docker Deployment

1. Build the image:

```bash
docker build -t clinix-backend:latest .
```

2. Run with docker-compose:

```bash
docker-compose -f docker/docker-compose.prod.yml up -d
```

### Environment-Specific Notes

| Environment | Considerations |
|-------------|----------------|
| **Development** | `DEBUG=true`, auto-reload enabled, local PostgreSQL/Redis |
| **Staging** | `DEBUG=false`, Chekk sandbox API, Twilio test credentials |
| **Production** | `DEBUG=false`, TLS 1.3, bcrypt rounds=12, rate limiting enabled, Chekk production API |

### Health Check

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "version": "1.0.0"
}
```

---

## MCP Action Skills

Clinix uses the Model Context Protocol (MCP) to trigger agentic workflows. Skills are defined in `app/services/ai_service.py`.

### Active Skills (MVP)

| Skill | Trigger | Actions |
|-------|---------|---------|
| `malaria_detect` | Fever + headache + chills | RDT stock check, Coartem availability, Day 3 follow-up |
| `cardiac_alert` | Chest pain + SOB + age > 40 | ECG order, cardiology referral, troponin check |
| `diabetes_mgmt` | RBS > 200 or known diabetic | Insulin stock check, HbA1c suggestion |
| `prenatal_screen` | Pregnant patient | Gestational tracking, high-risk flags |

All skills return structured output and require human verification before execution.

---

## Contributing

We follow a trunk-based development workflow.

### Branch Naming

- `feature/description` — New features
- `bugfix/description` — Bug fixes
- `hotfix/description` — Critical production fixes

### Commit Convention

```
feat: add supervisor batch approval
fix: correct AI confidence calculation
docs: update API endpoint documentation
test: add encounter finalization tests
```

### Pull Request Checklist

- [ ] Code follows PEP 8 style guidelines
- [ ] All tests pass (`pytest`)
- [ ] New features include tests
- [ ] API changes are documented in Swagger/ReDoc
- [ ] Database migrations are included if schema changed
- [ ] `.env.example` is updated if new env vars are added

### Setup Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

---

## Security

- All patient data is encrypted at rest (AES-256) and in transit (TLS 1.3)
- JWT tokens expire every 15 minutes; refresh tokens last 7 days
- Passwords hashed with bcrypt (12 rounds in production)
- PHI is never logged to application logs
- Rate limiting: 100 req/min per IP, 1000 req/min per authenticated user
- CORS is restricted to whitelisted production domains

Report security vulnerabilities to `security@clinix.ng`.

---

## Troubleshooting

### Database connection refused

```bash
# Check PostgreSQL is running
sudo service postgresql status
# Or with Docker
docker-compose ps
```

### Alembic migration conflicts

```bash
alembic stamp head
alembic upgrade head
```

### Redis connection errors

```bash
redis-cli ping
# Should return PONG
```

### OpenAI API rate limits

The application implements exponential backoff for OpenAI API calls. Check `app/services/ai_service.py` for retry configuration.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Contact

- **Team**: Clinix Engineering Team
- **Repository**: [https://github.com/Pioneer-Devs/clinix-backend](https://github.com/Pioneer-Devs/clinix-backend)

---

> *Built by Nigerian builders, for Nigerian students and patients.*

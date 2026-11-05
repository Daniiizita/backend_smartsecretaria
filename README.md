# SmartSecretaria API

A school-management REST API built with Django and Django REST Framework. It manages students, teachers, classes, enrollments, documents and user accounts, with role-based access control enforced on the server, not just in the UI.

> **Status:** portfolio project under active development. Do not use real student data, and do not use the development server in production. The frontend does not yet cover every module exposed by the API.

Frontend repository: [frontend_smartsecretaria](https://github.com/Daniiizita/frontend_smartsecretaria) (React + TypeScript).

## Tech stack

| Area | Technology |
| --- | --- |
| Language / framework | Python, Django 5.2, Django REST Framework 3.17 |
| Authentication | JWT via `djangorestframework-simplejwt` (refresh-token rotation + blacklist) |
| API docs | OpenAPI 3 via `drf-spectacular` (Swagger UI) |
| Database | SQLite (default; path configurable with `SQLITE_PATH`) |
| Serving | Gunicorn + WhiteNoise (static files) |
| Other libraries | `django-cors-headers`, `reportlab`, `openpyxl`, `Pillow` / `pillow-heif` |
| CI | GitHub Actions: `check`, pending-migrations check, test suite, `pip-audit` |
| Deployment (demo) | Render blueprint ([`render.yaml`](render.yaml)) |

## Key features

- **REST API** for students, teachers, classes, subjects, enrollments, calendar events, documents, users, notifications and a dashboard endpoint.
- **JWT authentication** with short-lived access tokens, rotating refresh tokens and a logout endpoint that blacklists the refresh token.
- **Server-side authorization by role** (administrator, secretary, teacher, guardian). Both row-level scoping (which records a user can see) and field-level scoping (which fields they can see) are enforced in the API.
- **Login rate limiting** per IP address, configurable via `LOGIN_THROTTLE_RATE`.
- **Audit data**: activity logs and login attempts are exposed as read-only endpoints, restricted to administrators.
- **Interactive API documentation**: OpenAPI schema at `/api/schema/` and Swagger UI at `/api/docs/`.
- **Health-check endpoint** at `/api/saude/`, used by the hosting provider and to wake up the free-tier server.
- **Demo mode**: the `seed_demo` management command generates a fictional school (classes, teachers, students) and demo accounts; `DEMO_MODE` protects those accounts from changes on a public demo.
- **Automated tests**: 157 tests covering permissions, row-level scoping, deletion protection, token security and the demo seed.

## Access roles

| Role | What it can do |
| --- | --- |
| Administrator | Full control, including secretary and other administrator accounts. Only superusers can modify superuser accounts. |
| Secretary | Manages the school (students, teachers, classes, assignments, enrollments, documents, calendar) and the accounts of teachers, guardians and students. |
| Teacher | Read-only: the classes they teach, the pedagogical data of their students, and basic data of their colleagues. |
| Guardian | Read-only: data, enrollments and documents of their own dependents, and basic data of those dependents' teachers. |

Every user can read their own profile at `/api/usuarios/me/` and change their own password at `/api/usuarios/me/senha/`.

These rules reflect a portfolio demo. Real use with children's data would require validation with the school or education authority and a professional data-protection review (LGPD, the Brazilian data-protection law).

## Getting started

### Prerequisites

- Python 3.12 (the version used in CI) or a version compatible with the pinned dependencies in `requirements.txt`

### Installation

On Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
mkdir -p data
```

On Windows (PowerShell):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
New-Item -ItemType Directory -Force data | Out-Null
```

### Configuration

`SECRET_KEY` is required. Copy [`.env.example`](.env.example) to `.env` and fill it in, or generate a key and export it:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Set `DEBUG=true` for local development. Every setting is read from environment variables and documented in `.env.example`. Never commit `.env`, SQLite databases or passwords.

### Run

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

The API is then available at `http://127.0.0.1:8000/api/`, with Swagger UI at `http://127.0.0.1:8000/api/docs/`.

### Demo data

To explore the system with fictional data (an invented school, classes, teachers and students):

```bash
python manage.py seed_demo
```

This creates the accounts `admin_demo`, `secretaria_demo`, `professor_demo` and `responsavel_demo`. The password is generated and printed once; you can also pass it with `--senha` or the `DEMO_PASSWORD` environment variable. Generated CPF numbers (Brazilian tax IDs) intentionally have an invalid check digit so they can never match a real person.

If school data already exists, the command refuses to run. `python manage.py seed_demo --reset` wipes all school data and the `*_demo` accounts (after asking for confirmation) and recreates the demo.

### Run the tests

```bash
python manage.py test
```

CI (GitHub Actions) runs `check`, a pending-migrations check, the test suite and `pip-audit` on every push or pull request to `develop` and `main`.

## Technical highlight: authorization enforced in the API, layered by row and by field

The frontend hides menus and buttons by role, but that is only a convenience. The real guarantees live in the API:

- [`core/permissions.py`](core/permissions.py) defines the role helpers and DRF permission classes, including which account types each role is allowed to manage.
- [`core/escopo.py`](core/escopo.py) implements **row-level scoping**: functions such as `turmas_visiveis(user)` and `alunos_visiveis(user)` return only the querysets a given role may see (for example, a guardian only sees classes and students linked to their dependents).
- **Field-level scoping** lives in each app's serializers (for example, teachers receive only the pedagogical fields of a student).
- Dedicated test modules (`tests_escopo_registros.py`, `tests_permissoes.py`, `tests_seguranca_tokens.py`, `tests_exclusao.py`) cover these rules.

The refresh-token flow is hardened too: refresh tokens rotate on every use and the previous one is blacklisted, so a leaked token stops working after its next use.

## Deploying the demo

The step-by-step guide to publish the free demo (API on Render, frontend on Vercel) is in [DEPLOY.md](DEPLOY.md). All settings come from environment variables, documented in [.env.example](.env.example).

Note that the demo runs on a free tier: the service sleeps after about 15 minutes of inactivity, and the first request afterwards can take up to a minute.

## Docker

A [`Dockerfile`](Dockerfile) and [`docker-compose.yml`](docker-compose.yml) are included for development (the compose file runs Django's `runserver` and reads settings from `.env`).

<!-- TODO: confirmar — o Dockerfile usa python:3.11-slim-buster, enquanto o CI e este README usam Python 3.12; confirmar se o fluxo com Docker ainda funciona e qual versão recomendar. -->

## License and authorship

Copyright (c) 2025 Danielle. See [LICENSE](LICENSE) for the terms of use. Commercial use requires prior written permission from the copyright holder.

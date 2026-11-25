# KafalatCare

KafalatCare is organized into a Django backend, a Django-rendered frontend, and a
separate Flask AI service. The AI service analyzes health-record patterns when an
authorized staff member requests an analysis from a child's Health Timeline.

## Project layout

```text
backend/       Django project, apps, management commands, and scripts
frontend/      Shared Django templates and static assets
ai_service/    Flask API, rule-based health analysis, tests, and API contract
media/         User-uploaded files (kept at the repository root)
db.sqlite3     Local database (kept at the repository root)
```

The root `requirements.txt` includes the backend and AI-service dependency files.
The `.env` file also stays at the repository root so both services can load the same
configuration.

## Setup

Requires Python 3.10+.

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `AI_SERVICE_API_KEY` in `.env` to a private value before using the integration.
Both Django and Flask read this same setting.

Sponsor notifications are stored in the application and are also sent by email when
SMTP is configured. Set `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`,
`EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, and `DEFAULT_FROM_EMAIL` in `.env`.
Without `EMAIL_HOST`, Django prints notification emails to the development console;
it does not deliver them to inboxes.

## Run

From the repository root, start Django in one terminal:

```powershell
python backend\manage.py migrate
python backend\manage.py runserver
```

In another terminal, start the AI service:

```powershell
python -m ai_service.run
```

Django is available at `http://127.0.0.1:8000/`. The AI health check is
`http://127.0.0.1:5000/health`.

## Health-pattern analysis

On a child's **Health Timeline**, staff can click **Analyze Health Patterns**. Django
sends that child's saved temperatures, symptoms, and parseable kilogram weights to
the rule-based service. Results are suggestions for staff review, not a medical
diagnosis.

## Sponsor workflow

Sponsors must provide a phone number and 13-digit CNIC and accept the displayed
minimum-one-month sponsorship terms when submitting a request. After admin approval
and matching, the sponsor's child page shows health, education, attendance, and meal
progress. Sponsors can message active staff members from that page. Notifications
are private to the sponsor, staff member, or administrator involved; emails contain
generic update notices rather than private child health details.

Run `python backend\manage.py migrate` after pulling changes to create the sponsorship
agreement, conversation, and notification tables.

## Tests

```powershell
python -m pytest -q ai_service\tests
python backend\manage.py test children.tests
```

## AI-service development

1. Put analysis rules in `ai_service/app/services/`.
2. Add HTTP endpoints in `ai_service/app/routes/`.
3. Register routes in `ai_service/app/__init__.py`.
4. Update `ai_service/docs/API_CONTRACT.md`.

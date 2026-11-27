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
Create a local `.env` from `.env.example`; do not commit or share the real `.env`.
Both services load their configuration from that root-level file.

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
and matching, the sponsor must complete the first installment through Safepay.
Child identity, education and care details, progress tracking, and staff messaging
remain private until a verified Safepay webhook confirms that first payment. After
verification, the active sponsor can access the matched child's profile, health,
education, attendance, and meal progress and message active staff members. Each
account can have only one pending or current sponsorship at a time, and matching
assigns at most one child to that account; another request is allowed after a
request is rejected or a sponsorship ends. Notifications are private to the sponsor,
staff member, or administrator involved; emails contain generic update notices
rather than private child health details.

Run `python backend\manage.py migrate` after pulling changes to create the sponsorship
agreement, conversation, and notification tables.

## Safepay payments

Donor online donations and approved sponsor installments use Safepay hosted checkout.
Checkout sessions default to sandbox. Add the Safepay API key, secret key, and webhook
shared secret to the root `.env` as `SAFEPAY_API_KEY`, `SAFEPAY_SECRET_KEY`, and
`SAFEPAY_WEBHOOK_SECRET`; do not paste or commit these credentials. Set
`SAFEPAY_ENV=sandbox` and `SITE_URL` to the public base URL for this Django instance.
For live transactions, use production credentials and set `SAFEPAY_ENV=production`;
tracker verification uses the same configured environment as checkout.
The origin from `SITE_URL` is trusted for CSRF automatically. For other browser
origins, add their full scheme and hostname (for example, `https://example.test`)
to the comma-separated `CSRF_TRUSTED_ORIGINS` setting. When testing webhooks through
a tunnel, also add that tunnel hostname to `ALLOWED_HOSTS`.

Configure the Safepay sandbox endpoint as `<SITE_URL>/payments/webhook/` and subscribe
to `payment.succeeded` and `payment.failed`. A payment is marked paid only after a
valid HMAC-signed webhook or an authenticated server-side tracker lookup with the
expected tracker, amount, currency, and completed state. Browser return parameters
alone never confirm a payment.

Each checkout charges once. Monthly sponsorship installments and monthly/quarterly
donation selections require a new manual checkout; automatic recurring billing is
not enabled. Admins can continue to record offline donations through the existing
donation management form.

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

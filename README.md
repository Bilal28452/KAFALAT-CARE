# KafalatCare: AI Service

A Python/Flask microservice. The backend calls it over HTTP. It is never mixed into the
frontend or backend code.

## Setup (first time)
```bash
python -m venv venv
# Windows:   venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # Windows: copy .env.example .env  (then edit the key in .env)
```
Requires Python 3.10+.

## Run
```bash
python run.py               # http://localhost:5000
```
Check: open `http://localhost:5000/health` in a browser.

## Test
```bash
python -m pytest -q
```

## Folder structure
```
app/
  __init__.py          creates the Flask app and registers routes
  config.py            settings (from .env)
  auth.py              X-API-Key check
  routes/              HTTP endpoints (thin layer: input/output only)
  services/            the real AI logic (rules, ML models)
tests/                 automated tests
docs/API_CONTRACT.md   agreement with the backend (read this first)
```
Rule of thumb: **keep routes thin and put logic in `services/`.** This makes testing and merging easy.

## Adding a new AI feature
1. Write the logic and tests in `app/services/<feature>.py`
2. Add the endpoint in `app/routes/<feature>.py`
3. Register the blueprint in `app/__init__.py`
4. Document the endpoint in `docs/API_CONTRACT.md`

## Git
`.env` and large model files are listed in `.gitignore` and will not be pushed to GitHub.

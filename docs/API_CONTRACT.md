# KafalatCare AI Service: API Contract (v1)

The agreement between the backend and the AI service. Both developers must agree on it.
If anything changes in this file, tell the other developer.

Base URL (local): `http://localhost:5000`
Every request (except `/health`) must include the header: `X-API-Key: <AI_SERVICE_API_KEY>`
Error format: `{ "error": "<code>", "message": "<human-readable text>" }`

---

## GET /health
Checks that the service is alive.
Response `200`: `{ "status": "ok", "service": "kafalatcare-ai" }`

---

## POST /health-pattern   (Status: READY)
Analyses a child's health records and returns alerts (rule-based).

**When to call:** whenever staff save a new health record. The backend sends the last
~30 days of records (including the latest one).

Request:
```json
{
  "child_id": 17,
  "records": [
    { "date": "2026-03-01", "weight_kg": 30.0, "temperature_c": 36.8, "symptoms": [] },
    { "date": "2026-03-10", "weight_kg": 29.0, "temperature_c": 38.4, "symptoms": ["cough"] }
  ]
}
```
- `date` is required, format `YYYY-MM-DD`
- `weight_kg` and `temperature_c` are optional (may be null)
- `symptoms` is an optional list of text values

Response `200`:
```json
{
  "child_id": 17,
  "alerts": [
    {
      "code": "FEVER_WITH_RESPIRATORY",
      "severity": "high",
      "message": "Fever together with cough/cold symptoms. A doctor's assessment is recommended.",
      "evidence": { "temperature_c": 38.4, "symptoms": ["cough"] },
      "source": "rule_based",
      "ai_suggested": true,
      "needs_staff_review": true
    }
  ],
  "alert_count": 1,
  "analyzed_records": 2,
  "latest_record_date": "2026-03-10",
  "note": "AI Suggested. Staff make the final decision."
}
```
Alert codes: `FEVER`, `FEVER_WITH_RESPIRATORY`, `PERSISTENT_FEVER`, `WEIGHT_LOSS`, `REPEATED_ILLNESS`
Severity: `high` | `medium` | `low`

**Backend responsibility:** save each alert in the `ai_alerts` table (code, severity, message,
evidence, child_id, status = "pending_review") and show it on the staff dashboard.

Errors: `400 validation_error`, `401 unauthorized`

---

## Upcoming endpoints (not built yet)
`/progress-monitor`, `/risk-score`, `/match`, `/forecast`, `/summarize`, `/generate-report`, `/chat`

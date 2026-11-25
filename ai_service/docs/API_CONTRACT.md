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

**When to call:** when an authorized staff member clicks **Analyze Health Patterns** on a
child's Health Timeline. The Django backend sends that child's saved health records.
The rules use the latest record and a rolling 30-day window where applicable.

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

The Django integration maps `last_checkup` to `date`, the optional `temperature_c` field to
`temperature_c`, parseable kilogram weights to `weight_kg`, and comma/semicolon/newline-separated
symptoms to `symptoms`. Results are shown on the child's Health Timeline for staff review;
they are not persisted as medical records or treated as a diagnosis.

Errors: `400 validation_error`, `401 unauthorized`

---

## Upcoming endpoints (not built yet)
`/progress-monitor`, `/risk-score`, `/match`, `/forecast`, `/summarize`, `/generate-report`, `/chat`

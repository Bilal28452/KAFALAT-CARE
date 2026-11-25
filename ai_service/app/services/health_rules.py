"""
Health Pattern Detection (rule-based AI).

Input : a child's health records (weight, temperature, symptoms) with dates.
Output: a list of alerts. Every alert is "AI Suggested"; staff make the final decision.

All rules live in this one file so staff and examiners can see
WHY an alert was raised (explainable).
"""
from datetime import datetime

# ---- Thresholds (easy to adjust in one place) ----
FEVER_C = 38.0
HIGH_FEVER_C = 39.5
WEIGHT_LOSS_MEDIUM_PCT = 5.0
WEIGHT_LOSS_HIGH_PCT = 10.0
WINDOW_DAYS = 30
REPEATED_ILLNESS_COUNT = 3
PERSISTENT_FEVER_RECORDS = 3
RESPIRATORY_SYMPTOMS = {"cough", "cold", "runny nose", "sore throat"}

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


class ValidationError(Exception):
    pass


def _parse_records(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Body must be a JSON object")
    if "child_id" not in payload:
        raise ValidationError("'child_id' is required")
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        raise ValidationError("'records' must be a non-empty list")

    parsed = []
    for i, r in enumerate(records):
        if not isinstance(r, dict):
            raise ValidationError(f"records[{i}] must be an object")
        try:
            d = datetime.strptime(str(r["date"]), "%Y-%m-%d").date()
        except (KeyError, ValueError):
            raise ValidationError(f"records[{i}].date must be in 'YYYY-MM-DD' format")

        weight = r.get("weight_kg")
        temp = r.get("temperature_c")
        for name, val in (("weight_kg", weight), ("temperature_c", temp)):
            if val is not None and (isinstance(val, bool) or not isinstance(val, (int, float))):
                raise ValidationError(f"records[{i}].{name} must be a number")
        if weight is not None and not (1 <= weight <= 200):
            raise ValidationError(f"records[{i}].weight_kg is not a plausible value")
        if temp is not None and not (30 <= temp <= 45):
            raise ValidationError(f"records[{i}].temperature_c is not a plausible value")

        symptoms = r.get("symptoms") or []
        if not isinstance(symptoms, list):
            raise ValidationError(f"records[{i}].symptoms must be a list")
        symptoms = [str(s).strip().lower() for s in symptoms if str(s).strip()]

        parsed.append({"date": d, "weight": weight, "temp": temp, "symptoms": symptoms})

    parsed.sort(key=lambda x: x["date"])
    return parsed


def _is_ill(rec):
    return (rec["temp"] is not None and rec["temp"] >= FEVER_C) or bool(rec["symptoms"])


def _alert(code, severity, message, evidence):
    return {
        "code": code,
        "severity": severity,
        "message": message,
        "evidence": evidence,
        "source": "rule_based",
        "ai_suggested": True,
        "needs_staff_review": True,
    }


def analyze_health_records(payload):
    records = _parse_records(payload)
    latest = records[-1]
    window = [r for r in records if (latest["date"] - r["date"]).days <= WINDOW_DAYS]
    alerts = []

    # Rule 1: Fever
    if latest["temp"] is not None and latest["temp"] >= FEVER_C:
        sev = "high" if latest["temp"] >= HIGH_FEVER_C else "medium"
        alerts.append(_alert(
            "FEVER", sev,
            f"Fever recorded ({latest['temp']}°C). Staff should decide whether a medical check is needed.",
            {"date": latest["date"].isoformat(), "temperature_c": latest["temp"]},
        ))

        # Rule 2: Fever together with respiratory symptoms
        found = sorted(set(latest["symptoms"]) & RESPIRATORY_SYMPTOMS)
        if found:
            alerts.append(_alert(
                "FEVER_WITH_RESPIRATORY", "high",
                "Fever together with cough/cold symptoms. A doctor's assessment is recommended.",
                {"temperature_c": latest["temp"], "symptoms": found},
            ))

    # Rule 3: Persistent fever (N consecutive records)
    last_n = records[-PERSISTENT_FEVER_RECORDS:]
    if len(last_n) == PERSISTENT_FEVER_RECORDS and all(
        r["temp"] is not None and r["temp"] >= FEVER_C for r in last_n
    ):
        alerts.append(_alert(
            "PERSISTENT_FEVER", "high",
            f"Fever recorded in {PERSISTENT_FEVER_RECORDS} consecutive records.",
            {"dates": [r["date"].isoformat() for r in last_n]},
        ))

    # Rule 4: Weight loss (compared with the highest weight in the window)
    weights = [(r["date"], r["weight"]) for r in window if r["weight"] is not None]
    if len(weights) >= 2 and latest["weight"] is not None:
        peak_date, peak = max(weights, key=lambda x: x[1])
        drop_pct = (peak - latest["weight"]) / peak * 100
        if drop_pct >= WEIGHT_LOSS_MEDIUM_PCT:
            sev = "high" if drop_pct >= WEIGHT_LOSS_HIGH_PCT else "medium"
            alerts.append(_alert(
                "WEIGHT_LOSS", sev,
                f"Weight dropped by {drop_pct:.1f}% within {WINDOW_DAYS} days.",
                {"from_kg": peak, "to_kg": latest["weight"], "drop_percent": round(drop_pct, 1),
                 "peak_date": peak_date.isoformat()},
            ))

    # Rule 5: Repeated illness
    ill_count = sum(1 for r in window if _is_ill(r))
    if ill_count >= REPEATED_ILLNESS_COUNT:
        alerts.append(_alert(
            "REPEATED_ILLNESS", "medium",
            f"{ill_count} illness records in the last {WINDOW_DAYS} days.",
            {"illness_records": ill_count, "window_days": WINDOW_DAYS},
        ))

    alerts.sort(key=lambda a: SEVERITY_ORDER[a["severity"]])
    return {
        "child_id": payload["child_id"],
        "alerts": alerts,
        "alert_count": len(alerts),
        "analyzed_records": len(records),
        "latest_record_date": latest["date"].isoformat(),
        "note": "AI Suggested. Staff make the final decision.",
    }

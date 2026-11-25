import pytest

from ai_service.app import create_app
from ai_service.app.services.health_rules import ValidationError, analyze_health_records


def rec(d, w=None, t=None, s=None):
    return {"date": d, "weight_kg": w, "temperature_c": t, "symptoms": s or []}


def codes(result):
    return {a["code"] for a in result["alerts"]}


def test_healthy_child_no_alerts():
    r = analyze_health_records({"child_id": 1, "records": [
        rec("2026-03-01", 30, 36.8), rec("2026-03-08", 30.2, 36.7)]})
    assert r["alert_count"] == 0


def test_fever_medium_and_high():
    r = analyze_health_records({"child_id": 1, "records": [rec("2026-03-01", 30, 38.4)]})
    assert codes(r) == {"FEVER"} and r["alerts"][0]["severity"] == "medium"
    r = analyze_health_records({"child_id": 1, "records": [rec("2026-03-01", 30, 39.8)]})
    assert r["alerts"][0]["severity"] == "high"


def test_fever_with_cough():
    r = analyze_health_records({"child_id": 1, "records": [
        rec("2026-03-01", 30, 38.5, ["Cough"])]})
    assert {"FEVER", "FEVER_WITH_RESPIRATORY"} <= codes(r)
    assert r["alerts"][0]["severity"] == "high"  # high severity is listed first


def test_weight_loss():
    r = analyze_health_records({"child_id": 1, "records": [
        rec("2026-03-01", 30), rec("2026-03-10", 29), rec("2026-03-20", 27.5)]})
    a = [x for x in r["alerts"] if x["code"] == "WEIGHT_LOSS"][0]
    assert a["severity"] == "medium" and a["evidence"]["drop_percent"] == 8.3


def test_old_weight_outside_window_ignored():
    r = analyze_health_records({"child_id": 1, "records": [
        rec("2026-01-01", 40), rec("2026-03-20", 30)]})
    assert "WEIGHT_LOSS" not in codes(r)


def test_persistent_fever():
    r = analyze_health_records({"child_id": 1, "records": [
        rec("2026-03-01", t=38.2), rec("2026-03-02", t=38.5), rec("2026-03-03", t=38.1)]})
    assert "PERSISTENT_FEVER" in codes(r)


def test_repeated_illness():
    r = analyze_health_records({"child_id": 1, "records": [
        rec("2026-03-01", s=["cold"]), rec("2026-03-10", t=38.1), rec("2026-03-20", s=["cough"])]})
    assert "REPEATED_ILLNESS" in codes(r)


@pytest.mark.parametrize("bad", [
    {}, {"child_id": 1}, {"child_id": 1, "records": []},
    {"child_id": 1, "records": [{"date": "01-03-2026"}]},
    {"child_id": 1, "records": [rec("2026-03-01", t=99)]},
    {"child_id": 1, "records": [rec("2026-03-01", w="abc")]},
])
def test_validation_errors(bad):
    with pytest.raises(ValidationError):
        analyze_health_records(bad)


def test_http_endpoint_and_api_key():
    app = create_app({"TESTING": True, "AI_SERVICE_API_KEY": "secret"})
    c = app.test_client()
    body = {"child_id": 5, "records": [rec("2026-03-01", 30, 39.0)]}
    assert c.get("/health").status_code == 200
    assert c.post("/health-pattern", json=body).status_code == 401
    ok = c.post("/health-pattern", json=body, headers={"X-API-Key": "secret"})
    assert ok.status_code == 200 and ok.get_json()["alert_count"] >= 1
    bad = c.post("/health-pattern", json={"child_id": 5}, headers={"X-API-Key": "secret"})
    assert bad.status_code == 400

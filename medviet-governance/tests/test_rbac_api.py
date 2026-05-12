import pandas as pd
from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_missing_token_returns_401():
    response = client.get("/api/patients/raw")
    assert response.status_code == 401


def test_admin_can_read_raw_patients():
    response = client.get("/api/patients/raw", headers=auth("token-alice"))
    assert response.status_code == 200
    records = response.json()
    assert len(records) == 10
    assert "cccd" in records[0]


def test_ml_engineer_cannot_read_raw_patients():
    response = client.get("/api/patients/raw", headers=auth("token-bob"))
    assert response.status_code == 403


def test_ml_engineer_and_admin_can_read_anonymized_patients():
    for token in ("token-alice", "token-bob"):
        response = client.get("/api/patients/anonymized", headers=auth(token))
        assert response.status_code == 200
        records = response.json()
        assert len(records) == 10


def test_data_analyst_can_read_aggregated_metrics():
    response = client.get("/api/metrics/aggregated", headers=auth("token-carol"))
    assert response.status_code == 200
    body = response.json()
    assert body["total_patients"] == 200
    assert "patients_by_disease" in body


def test_intern_cannot_access_production_endpoints():
    for path in (
        "/api/patients/raw",
        "/api/patients/anonymized",
        "/api/metrics/aggregated",
    ):
        response = client.get(path, headers=auth("token-dave"))
        assert response.status_code == 403


def test_only_admin_can_delete_patient():
    patient_id = pd.read_csv("data/raw/patients_raw.csv").iloc[0]["patient_id"]

    denied = client.delete(f"/api/patients/{patient_id}", headers=auth("token-bob"))
    assert denied.status_code == 403

    allowed = client.delete(f"/api/patients/{patient_id}", headers=auth("token-alice"))
    assert allowed.status_code == 200
    assert allowed.json()["patient_id"] == patient_id

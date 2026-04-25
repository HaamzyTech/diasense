from uuid import uuid4

import httpx
import pytest

from app.api.v1.endpoints import predict as predict_endpoint
from app.main import app


class DummyService:
    def create_prediction(self, payload: dict) -> dict:
        assert payload["glucose"] == 138.0
        return {
            "request_id": uuid4(),
            "model_version_id": uuid4(),
            "predicted_label": True,
            "risk_probability": 0.8123,
            "risk_band": "high",
            "interpretation": "High predicted diabetes risk. This tool does not provide a medical diagnosis.",
            "top_factors": [
                {"feature": "glucose", "importance": 0.41},
                {"feature": "bmi", "importance": 0.22},
                {"feature": "age", "importance": 0.14},
            ],
            "latency_ms": 42,
            "created_at": "2026-04-21T12:00:00Z",
        }


@pytest.mark.anyio
async def test_predict_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(predict_endpoint, "get_prediction_service", lambda _db: DummyService())

    transport = httpx.ASGITransport(app=app)
    payload = {
        "session_id": "11111111-1111-1111-1111-111111111111",
        "actor_role": "patient",
        "pregnancies": 2,
        "glucose": 138,
        "blood_pressure": 72,
        "skin_thickness": 35,
        "insulin": 0,
        "bmi": 33.6,
        "diabetes_pedigree_function": 0.627,
        "age": 50,
    }
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/v1/predict", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["risk_band"] == "high"
    assert body["risk_probability"] == 0.8123
    assert body["interpretation"] == "High predicted diabetes risk. This tool does not provide a medical diagnosis."


@pytest.mark.anyio
async def test_predict_endpoint_rejects_invalid_payload() -> None:
    transport = httpx.ASGITransport(app=app)
    payload = {
        "session_id": "11111111-1111-1111-1111-111111111111",
        "actor_role": "patient",
        "pregnancies": -1,
        "glucose": 138,
        "blood_pressure": 72,
        "skin_thickness": 35,
        "insulin": 0,
        "bmi": 33.6,
        "diabetes_pedigree_function": 0.627,
        "age": 50,
    }
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/v1/predict", json=payload)
    assert response.status_code == 422

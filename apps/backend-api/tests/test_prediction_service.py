import pytest

from app.services.prediction_service import (
    PredictionService,
    derive_age_band,
    derive_bmi_group,
    interpretation_for_band,
    map_risk_band,
)


class DummyPredictionRepo:
    def create_request(self, payload):
        return {
            "id": "22222222-2222-2222-2222-222222222222",
            "source": payload["source"],
        }

    def create_result(self, payload):
        self.last_result = payload
        return {"id": "1", "created_at": "2026-04-21T12:00:00Z"}

    def get_prediction(self, _request_id):
        return None

    def list_predictions(self, _session_id, _limit):
        return []


class DummyModelRepo:
    def get_active(self):
        return {
            "id": "33333333-3333-3333-3333-333333333333",
            "model_name": "diasense-diabetes-risk",
            "model_version": "7",
        }


class DummyClient:
    def __init__(self) -> None:
        self.last_records = None

    def invoke(self, records):
        self.last_records = records
        return [
            {
                "predicted_label": True,
                "risk_probability": 0.9,
                "top_factors": [{"feature": "glucose", "importance": 0.8}],
            }
        ]


class DummySystemEventRepo:
    def create_event(self, *_args, **_kwargs):
        return None


def test_risk_band_mapping() -> None:
    assert map_risk_band(0.1) == "low"
    assert map_risk_band(0.33) == "moderate"
    assert map_risk_band(0.65) == "moderate"
    assert map_risk_band(0.66) == "high"


def test_interpretation_mapping() -> None:
    assert interpretation_for_band("low").startswith("Low predicted")
    assert interpretation_for_band("moderate").startswith("Moderate predicted")
    assert interpretation_for_band("high").startswith("High predicted")


@pytest.mark.parametrize(
    ("bmi", "expected"),
    [
        (18.5, "underweight"),
        (25.0, "normal"),
        (30.0, "overweight"),
        (30.1, "obese"),
    ],
)
def test_bmi_group_mapping(bmi: float, expected: str) -> None:
    assert derive_bmi_group(bmi) == expected


@pytest.mark.parametrize(
    ("age", "expected"),
    [
        (30, "young"),
        (45, "adult"),
        (60, "middle_age"),
        (61, "older"),
    ],
)
def test_age_band_mapping(age: int, expected: str) -> None:
    assert derive_age_band(age) == expected


def test_prediction_service_creates_contract_response() -> None:
    model_client = DummyClient()
    service = PredictionService(
        prediction_repo=DummyPredictionRepo(),
        model_repo=DummyModelRepo(),
        model_server_client=model_client,
        system_event_repo=DummySystemEventRepo(),
    )

    result = service.create_prediction(
        {
            "session_id": "11111111-1111-1111-1111-111111111111",
            "actor_role": "patient",
            "pregnancies": 2,
            "glucose": 138.0,
            "blood_pressure": 72.0,
            "skin_thickness": 35.0,
            "insulin": 0.0,
            "bmi": 33.6,
            "diabetes_pedigree_function": 0.627,
            "age": 50,
        }
    )

    assert result["risk_band"] == "high"
    assert result["predicted_label"] is True
    assert result["risk_probability"] == 0.9
    assert result["top_factors"][0]["feature"] == "glucose"
    assert model_client.last_records == [
        {
            "pregnancies": 2,
            "glucose": 138.0,
            "blood_pressure": 72.0,
            "skin_thickness": 35.0,
            "insulin": 0.0,
            "bmi": 33.6,
            "bmi_group": "obese",
            "diabetes_pedigree_function": 0.627,
            "age": 50,
            "age_band": "middle_age",
        }
    ]

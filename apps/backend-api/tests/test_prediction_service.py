import pytest

from app.core.auth_context import CurrentUser
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
            "mlflow_model_uri": "models:/diasense-diabetes-risk/7",
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

    def predict_probability(self, _model_uri, _records):
        return 0.9


class DummyLabelOnlyClient:
    def __init__(self) -> None:
        self.last_records = None
        self.last_probability_request = None

    def invoke(self, records):
        self.last_records = records
        return [1]

    def predict_probability(self, model_uri, records):
        self.last_probability_request = (model_uri, records)
        return 0.7345


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
            "pregnancies": 2,
            "glucose": 138.0,
            "blood_pressure": 72.0,
            "skin_thickness": 35.0,
            "insulin": 0.0,
            "bmi": 33.6,
            "diabetes_pedigree_function": 0.627,
            "age": 50,
        },
        current_user=CurrentUser(
            username="patient.one",
            email="patient@example.com",
            role="patient",
            auth_source="database",
            access_token="token",
        ),
    )

    assert result["risk_band"] == "high"
    assert result["predicted_label"] is True
    assert result["risk_probability"] == 0.9
    assert result["top_factors"][0]["feature"] == "glucose"
    assert result["submitted_by"] == "patient@example.com"
    assert result["patient_email"] == "patient@example.com"
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


def test_prediction_service_falls_back_to_registered_model_probability() -> None:
    model_client = DummyLabelOnlyClient()
    service = PredictionService(
        prediction_repo=DummyPredictionRepo(),
        model_repo=DummyModelRepo(),
        model_server_client=model_client,
        system_event_repo=DummySystemEventRepo(),
    )

    result = service.create_prediction(
        {
            "pregnancies": 1,
            "glucose": 121.0,
            "blood_pressure": 68.0,
            "skin_thickness": 20.0,
            "insulin": 85.0,
            "bmi": 27.4,
            "diabetes_pedigree_function": 0.391,
            "age": 38,
        },
        current_user=CurrentUser(
            username="clinician.one",
            email="clinician@example.com",
            role="clinician",
            auth_source="database",
            access_token="token",
        ),
    )

    assert result["predicted_label"] is True
    assert result["risk_probability"] == 0.7345
    assert model_client.last_probability_request == (
        "models:/diasense-diabetes-risk/7",
        [
            {
                "pregnancies": 1,
                "glucose": 121.0,
                "blood_pressure": 68.0,
                "skin_thickness": 20.0,
                "insulin": 85.0,
                "bmi": 27.4,
                "bmi_group": "overweight",
                "diabetes_pedigree_function": 0.391,
                "age": 38,
                "age_band": "adult",
            }
        ],
    )

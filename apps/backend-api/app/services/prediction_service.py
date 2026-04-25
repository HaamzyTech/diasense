from time import perf_counter
from uuid import UUID

from app.clients.model_server import ModelServerClient
from app.core.exceptions import DependencyError, NotFoundError, ValidationError
from app.core.time import to_iso8601
from app.metrics.prometheus import (
    MODEL_INFERENCE_LATENCY_MS,
    PREDICTION_ERRORS_TOTAL,
    PREDICTION_REQUESTS_TOTAL,
)
from app.repositories.model_version_repository import ModelVersionRepository
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.system_event_repository import SystemEventRepository


def map_risk_band(probability: float) -> str:
    if probability < 0.33:
        return "low"
    if probability < 0.66:
        return "moderate"
    return "high"


def interpretation_for_band(risk_band: str) -> str:
    mapping = {
        "low": "Low predicted diabetes risk. This tool does not provide a medical diagnosis.",
        "moderate": (
            "Moderate predicted diabetes risk. Consider discussing results with a healthcare professional. "
            "This tool does not provide a medical diagnosis."
        ),
        "high": "High predicted diabetes risk. This tool does not provide a medical diagnosis.",
    }
    return mapping[risk_band]


def derive_bmi_group(bmi: float) -> str:
    if bmi <= 18.5:
        return "underweight"
    if bmi <= 25.0:
        return "normal"
    if bmi <= 30.0:
        return "overweight"
    return "obese"


def derive_age_band(age: int) -> str:
    if age <= 30:
        return "young"
    if age <= 45:
        return "adult"
    if age <= 60:
        return "middle_age"
    return "older"


class PredictionService:
    def __init__(
        self,
        prediction_repo: PredictionRepository,
        model_repo: ModelVersionRepository,
        model_server_client: ModelServerClient,
        system_event_repo: SystemEventRepository | None = None,
    ) -> None:
        self.prediction_repo = prediction_repo
        self.model_repo = model_repo
        self.model_server_client = model_server_client
        self.system_event_repo = system_event_repo

    def create_prediction(self, payload: dict) -> dict:
        request_payload = {**payload, "source": payload.get("source", "web")}
        request_row = self.prediction_repo.create_request(request_payload)

        active_model = self.model_repo.get_active()
        if not active_model:
            PREDICTION_ERRORS_TOTAL.labels(reason="no_active_model").inc()
            raise DependencyError("No active model available for inference")

        try:
            started_at = perf_counter()
            model_output = self.model_server_client.invoke([self._model_input(payload)])
            latency_ms = max(int((perf_counter() - started_at) * 1000), 0)
            MODEL_INFERENCE_LATENCY_MS.set(latency_ms)
        except Exception:
            PREDICTION_ERRORS_TOTAL.labels(reason="model_server_error").inc()
            self._record_event(
                severity="error",
                message="Prediction failed while calling model-server",
                metadata={"request_id": str(request_row["id"])},
            )
            raise

        first_result = model_output[0] if model_output else {}
        probability = self._extract_probability(first_result)
        risk_band = map_risk_band(probability)
        interpretation = interpretation_for_band(risk_band)
        predicted_label = bool(first_result.get("predicted_label", probability >= 0.5))
        top_factors = self._extract_top_factors(first_result)

        result_row = self.prediction_repo.create_result(
            {
                "request_id": str(request_row["id"]),
                "model_version_id": str(active_model["id"]),
                "predicted_label": predicted_label,
                "risk_probability": round(probability, 4),
                "risk_band": risk_band,
                "explanation": {
                    "interpretation": interpretation,
                    "top_factors": top_factors,
                },
                "latency_ms": latency_ms,
            }
        )
        PREDICTION_REQUESTS_TOTAL.labels(risk_band=risk_band).inc()

        return {
            "request_id": request_row["id"],
            "model_version_id": UUID(str(active_model["id"])),
            "predicted_label": predicted_label,
            "risk_probability": round(probability, 4),
            "risk_band": risk_band,
            "interpretation": interpretation,
            "top_factors": top_factors,
            "latency_ms": latency_ms,
            "created_at": to_iso8601(result_row["created_at"]),
        }

    def get_prediction(self, request_id: UUID) -> dict:
        row = self.prediction_repo.get_prediction(request_id=request_id)
        if not row:
            raise NotFoundError(f"Prediction request {request_id} not found")

        explanation = row.get("explanation") or {}
        if isinstance(explanation, str):
            explanation = {}

        request = {
            "id": row["id"],
            "session_id": row["session_id"],
            "actor_role": row["actor_role"],
            "pregnancies": row["pregnancies"],
            "glucose": float(row["glucose"]),
            "blood_pressure": float(row["blood_pressure"]),
            "skin_thickness": float(row["skin_thickness"]),
            "insulin": float(row["insulin"]),
            "bmi": float(row["bmi"]),
            "diabetes_pedigree_function": float(row["diabetes_pedigree_function"]),
            "age": row["age"],
            "source": row["source"],
            "created_at": to_iso8601(row["created_at"]),
        }
        if row.get("result_id") is None:
            return {"request": request, "result": None}

        result = {
            "id": row["result_id"],
            "model_version_id": row["model_version_id"],
            "predicted_label": row["predicted_label"],
            "risk_probability": round(float(row["risk_probability"]), 4),
            "risk_band": row["risk_band"],
            "interpretation": explanation.get("interpretation", interpretation_for_band(str(row["risk_band"]))),
            "top_factors": explanation.get("top_factors", []),
            "latency_ms": row["latency_ms"],
            "created_at": to_iso8601(row["result_created_at"]),
        }
        return {"request": request, "result": result}

    def list_predictions(self, session_id: UUID, limit: int = 20) -> dict:
        items = self.prediction_repo.list_predictions(session_id=session_id, limit=limit)
        normalized_items: list[dict] = []
        for item in items:
            explanation = item.get("explanation") or {}
            if isinstance(explanation, str):
                explanation = {}
            normalized_items.append(
                {
                    "request_id": item["request_id"],
                    "risk_probability": round(float(item["risk_probability"]), 4),
                    "risk_band": item["risk_band"],
                    "predicted_label": item["predicted_label"],
                    "interpretation": explanation.get(
                        "interpretation",
                        interpretation_for_band(str(item["risk_band"])),
                    ),
                    "created_at": to_iso8601(item["created_at"]),
                }
            )
        return {"session_id": session_id, "items": normalized_items, "count": len(normalized_items)}

    def _extract_probability(self, payload: dict) -> float:
        probability = payload.get("risk_probability", payload.get("probability"))
        try:
            probability_value = float(probability)
        except (TypeError, ValueError) as exc:
            raise ValidationError("Model-server returned an invalid probability") from exc
        if not 0 <= probability_value <= 1:
            raise ValidationError("Model-server returned out-of-range probability")
        return probability_value

    def _extract_top_factors(self, payload: dict) -> list[dict]:
        top_factors = payload.get("top_factors", [])
        if not isinstance(top_factors, list):
            return []
        normalized: list[dict] = []
        for item in top_factors:
            if isinstance(item, dict) and "feature" in item and "importance" in item:
                normalized.append(
                    {
                        "feature": str(item["feature"]),
                        "importance": float(item["importance"]),
                    }
                )
        return normalized

    def _model_input(self, payload: dict) -> dict:
        return {
            "pregnancies": payload["pregnancies"],
            "glucose": payload["glucose"],
            "blood_pressure": payload["blood_pressure"],
            "skin_thickness": payload["skin_thickness"],
            "insulin": payload["insulin"],
            "bmi": payload["bmi"],
            "bmi_group": derive_bmi_group(float(payload["bmi"])),
            "diabetes_pedigree_function": payload["diabetes_pedigree_function"],
            "age": payload["age"],
            "age_band": derive_age_band(int(payload["age"])),
        }

    def _record_event(self, severity: str, message: str, metadata: dict) -> None:
        if self.system_event_repo is None:
            return
        try:
            self.system_event_repo.create_event(
                service_name="backend-api",
                severity=severity,
                message=message,
                metadata=metadata,
            )
        except Exception:
            return

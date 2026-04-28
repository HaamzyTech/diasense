from time import perf_counter
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from app.clients.model_server import ModelServerClient
from app.core.auth_context import CurrentUser
from app.core.exceptions import AuthorizationError, DependencyError, NotFoundError, ValidationError
from app.core.time import to_iso8601, utc_now
from app.metrics.prometheus import (
    MODEL_INFERENCE_LATENCY_MS,
    PREDICTION_ERRORS_TOTAL,
    PREDICTION_REQUESTS_TOTAL,
)
from app.repositories.auth_user_repository import AuthUserRepository
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
        auth_user_repo: AuthUserRepository | None = None,
    ) -> None:
        self.prediction_repo = prediction_repo
        self.model_repo = model_repo
        self.model_server_client = model_server_client
        self.system_event_repo = system_event_repo
        self.auth_user_repo = auth_user_repo

    def create_prediction(self, payload: dict, current_user: CurrentUser) -> dict:
        patient_email = self._resolve_patient_email(payload.get("patient_email"), current_user)
        model_input = self._model_input(payload)
        request_payload = {
            **payload,
            "session_id": self._session_id_for_patient(patient_email),
            "submitted_by": self._normalize_subject(current_user.email or current_user.username),
            "patient_email": patient_email,
            "actor_role": current_user.role,
            "source": payload.get("source", "web"),
        }
        request_row = self.prediction_repo.create_request(request_payload)

        active_model = self.model_repo.get_active()
        if not active_model:
            PREDICTION_ERRORS_TOTAL.labels(reason="no_active_model").inc()
            raise DependencyError("No active model available for inference")

        try:
            started_at = perf_counter()
            model_output = self.model_server_client.invoke([model_input])
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

        first_result = self._normalize_inference_result(model_output[0] if model_output else {})
        probability = self._resolve_probability(
            payload=first_result,
            active_model=active_model,
            model_input=model_input,
        )
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
            "submitted_by": request_payload["submitted_by"],
            "patient_email": patient_email,
            "predicted_label": predicted_label,
            "risk_probability": round(probability, 4),
            "risk_band": risk_band,
            "interpretation": interpretation,
            "top_factors": top_factors,
            "latency_ms": latency_ms,
            "created_at": to_iso8601(result_row["created_at"]),
        }

    def get_prediction(self, request_id: UUID, current_user: CurrentUser) -> dict:
        row = self.prediction_repo.get_prediction(request_id=request_id)
        if not row:
            raise NotFoundError(f"Prediction request {request_id} not found")
        self._ensure_prediction_access(row, current_user)

        explanation = row.get("explanation") or {}
        if isinstance(explanation, str):
            explanation = {}

        request = {
            "id": row["id"],
            "session_id": row["session_id"],
            "submitted_by": row["submitted_by"],
            "patient_email": row["patient_email"],
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

    def list_predictions(
        self,
        current_user: CurrentUser,
        limit: int = 20,
        patient_email: str | None = None,
    ) -> dict:
        normalized_patient_email = self._resolve_prediction_filter(patient_email, current_user)
        items = self.prediction_repo.list_predictions(limit=limit, patient_email=normalized_patient_email)
        normalized_items: list[dict] = []
        for item in items:
            explanation = item.get("explanation") or {}
            if isinstance(explanation, str):
                explanation = {}
            normalized_items.append(
                {
                    "request_id": item["request_id"],
                    "submitted_by": item["submitted_by"],
                    "patient_email": item["patient_email"],
                    "actor_role": item["actor_role"],
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
        return {"items": normalized_items, "count": len(normalized_items)}

    def list_my_predictions(self, current_user: CurrentUser, limit: int = 20) -> dict:
        return self.list_predictions(current_user=current_user, limit=limit, patient_email=self._current_reference(current_user))

    def delete_prediction(self, request_id: UUID, current_user: CurrentUser) -> dict:
        row = self.prediction_repo.get_prediction(request_id=request_id)
        if not row:
            raise NotFoundError(f"Prediction request {request_id} not found")
        self._ensure_prediction_access(row, current_user)

        deleted = self.prediction_repo.delete_prediction_request(request_id=request_id)
        if deleted is None:
            raise NotFoundError(f"Prediction request {request_id} not found")

        return {
            "message": "Prediction result deleted successfully",
            "request_id": deleted["id"],
            "patient_email": deleted["patient_email"],
            "submitted_by": deleted["submitted_by"],
            "actor_role": deleted["actor_role"],
            "deleted_at": to_iso8601(utc_now()),
        }

    def _resolve_probability(
        self,
        payload: dict,
        active_model: dict,
        model_input: dict,
    ) -> float:
        if payload.get("risk_probability") is not None or payload.get("probability") is not None:
            return self._extract_probability(payload)

        model_uri = str(active_model.get("mlflow_model_uri") or "").strip()
        if not model_uri:
            raise DependencyError("The active model does not expose a model URI for probability inference")

        probability_value = self.model_server_client.predict_probability(model_uri, [model_input])
        if not 0 <= probability_value <= 1:
            raise ValidationError("Model probability inference returned out-of-range probability")
        return probability_value

    def _normalize_inference_result(self, payload: Any) -> dict[str, Any]:
        if isinstance(payload, dict):
            return payload

        try:
            numeric_value = float(payload)
        except (TypeError, ValueError) as exc:
            raise ValidationError("Model-server returned an invalid prediction payload") from exc

        if numeric_value in {0.0, 1.0}:
            return {"predicted_label": bool(int(numeric_value))}

        return {"risk_probability": numeric_value}

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

    def _resolve_patient_email(self, patient_email: str | None, current_user: CurrentUser) -> str:
        current_subject = self._current_reference(current_user)
        requested_email = self._normalize_subject(patient_email) if patient_email else current_subject

        if current_user.role == "patient":
            if requested_email != current_subject:
                raise AuthorizationError("Patients can only submit assessments for themselves")
            return current_subject

        if requested_email == current_subject:
            return current_subject

        if current_user.role not in {"clinician", "admin"}:
            raise AuthorizationError()

        if self.auth_user_repo is None:
            raise ValidationError("Auth user repository is not configured")

        patient_user = self.auth_user_repo.get_by_identifier(requested_email)
        if patient_user is None:
            raise ValidationError("Patient account not found")
        return self._account_reference(patient_user)

    def _resolve_prediction_filter(self, patient_email: str | None, current_user: CurrentUser) -> str | None:
        if current_user.role == "patient":
            return self._current_reference(current_user)

        if patient_email is None or patient_email.strip() == "":
            return None

        requested_email = self._normalize_subject(patient_email)
        if requested_email == self._current_reference(current_user):
            return requested_email

        if current_user.role not in {"clinician", "admin"}:
            raise AuthorizationError()

        if self.auth_user_repo is None:
            raise ValidationError("Auth user repository is not configured")

        patient_user = self.auth_user_repo.get_by_identifier(requested_email)
        if patient_user is None:
            raise NotFoundError(f"Patient {requested_email} not found")
        return self._account_reference(patient_user)

    def _ensure_prediction_access(self, row: dict, current_user: CurrentUser) -> None:
        if current_user.role in {"clinician", "admin"}:
            return
        patient_email = self._normalize_subject(str(row["patient_email"]))
        if patient_email != self._current_reference(current_user):
            raise AuthorizationError("You do not have permission to view this prediction")

    def _session_id_for_patient(self, patient_email: str) -> UUID:
        return uuid5(NAMESPACE_URL, f"https://diasense.local/patients/{patient_email}")

    def _normalize_subject(self, subject: str | None) -> str:
        if subject is None:
            raise ValidationError("A patient account is required")
        normalized = subject.strip().lower()
        if not normalized:
            raise ValidationError("A patient account is required")
        return normalized

    def _current_reference(self, current_user: CurrentUser) -> str:
        return self._normalize_subject(current_user.email or current_user.username)

    def _account_reference(self, user: dict) -> str:
        return self._normalize_subject(str(user.get("email") or user["username"]))

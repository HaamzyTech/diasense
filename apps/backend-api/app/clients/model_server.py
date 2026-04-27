from functools import lru_cache
from math import exp
from typing import Any

import httpx
import pandas as pd

from app.core.config import get_settings
from app.core.exceptions import DependencyError


@lru_cache(maxsize=4)
def _load_registered_model(model_uri: str):
    try:
        import mlflow.sklearn
    except ImportError as exc:
        raise DependencyError("MLflow sklearn support is not installed in backend-api") from exc

    return mlflow.sklearn.load_model(model_uri)


class ModelServerClient:
    def __init__(self, base_url: str | None = None) -> None:
        settings = get_settings()
        self.base_url = (base_url or settings.model_server_url).rstrip("/")
        self.timeout = settings.request_timeout_seconds

    def ping(self) -> bool:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.base_url}/ping")
                return response.status_code < 500
        except httpx.HTTPError:
            return False

    def invoke(self, dataframe_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        payload = {"dataframe_records": dataframe_records}
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(f"{self.base_url}/invocations", json=payload)
                response.raise_for_status()
                return self._normalize_payload(response.json())
        except (httpx.HTTPError, ValueError) as exc:
            raise DependencyError(f"Failed to call model-server: {exc}") from exc

    def predict_probability(self, model_uri: str, dataframe_records: list[dict[str, Any]]) -> float:
        try:
            model = _load_registered_model(model_uri)
            frame = pd.DataFrame.from_records(dataframe_records)

            if hasattr(model, "predict_proba"):
                probabilities = model.predict_proba(frame)
                if getattr(probabilities, "ndim", 0) == 2 and probabilities.shape[1] >= 2:
                    return float(probabilities[0][1])

            if hasattr(model, "decision_function"):
                scores = model.decision_function(frame)
                if len(scores) > 0:
                    score = float(scores[0])
                    return float(1.0 / (1.0 + exp(-score)))
        except DependencyError:
            raise
        except Exception as exc:
            raise DependencyError(f"Failed to compute model probability from MLflow model: {exc}") from exc

        raise DependencyError("The active model does not expose probability scores")

    def _normalize_payload(self, payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            if all(isinstance(item, dict) for item in payload):
                return payload
            if payload:
                return [self._normalize_scalar_prediction(payload[0])]
            return []

        if isinstance(payload, dict):
            predictions = payload.get("predictions")
            if isinstance(predictions, list):
                if all(isinstance(item, dict) for item in predictions):
                    return predictions
                if predictions:
                    return [self._normalize_scalar_prediction(predictions[0])]
                return []

        raise DependencyError("Invalid model-server response format")

    def _normalize_scalar_prediction(self, value: Any) -> dict[str, Any]:
        try:
            numeric_value = float(value)
        except (TypeError, ValueError) as exc:
            raise DependencyError("Invalid scalar prediction returned by model-server") from exc

        if numeric_value in {0.0, 1.0}:
            return {"predicted_label": bool(int(numeric_value))}

        return {"risk_probability": numeric_value}

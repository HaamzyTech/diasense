from typing import Any

import httpx

from app.core.config import get_settings
from app.core.exceptions import DependencyError


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

    def _normalize_payload(self, payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            if all(isinstance(item, dict) for item in payload):
                return payload
            if payload:
                return [{"risk_probability": float(payload[0])}]
            return []

        if isinstance(payload, dict):
            predictions = payload.get("predictions")
            if isinstance(predictions, list):
                if all(isinstance(item, dict) for item in predictions):
                    return predictions
                if predictions:
                    return [{"risk_probability": float(predictions[0])}]
                return []

        raise DependencyError("Invalid model-server response format")

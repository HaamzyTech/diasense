import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.time import to_iso8601, utc_now


class HealthService:
    def __init__(self, settings: Settings, db: Session) -> None:
        self.settings = settings
        self.db = db

    def health(self) -> dict:
        return {
            "status": "ok",
            "service": self.settings.app_name,
            "version": self.settings.app_version,
            "timestamp": to_iso8601(utc_now()),
        }

    def ready(self) -> tuple[dict, bool]:
        dependencies = {
            "postgres": self._check_postgres(),
            "model_server": self._check_http(f"{self.settings.model_server_url.rstrip('/')}/ping"),
            "mlflow_tracking": self._check_http(self.settings.mlflow_tracking_uri),
        }
        is_ready = all(status == "ok" for status in dependencies.values())
        return (
            {
                "status": "ready" if is_ready else "not_ready",
                "service": self.settings.app_name,
                "version": self.settings.app_version,
                "dependencies": dependencies,
                "timestamp": to_iso8601(utc_now()),
            },
            is_ready,
        )

    def _check_postgres(self) -> str:
        try:
            self.db.execute(text("SELECT 1"))
            return "ok"
        except Exception:
            return "error"

    def _check_http(self, url: str) -> str:
        try:
            with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
                response = client.get(url)
                return "ok" if response.status_code < 500 else "error"
        except httpx.HTTPError:
            return "error"

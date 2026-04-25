from app.core.config import Settings
from app.core.time import to_iso8601, utc_now
from app.services.drift_service import DriftService
from app.services.health_service import HealthService
from app.services.model_registry_service import ModelRegistryService
from app.services.pipeline_service import PipelineService


class OpsService:
    def __init__(
        self,
        settings: Settings,
        health_service: HealthService,
        model_registry_service: ModelRegistryService,
        pipeline_service: PipelineService,
        drift_service: DriftService,
    ) -> None:
        self.settings = settings
        self.health_service = health_service
        self.model_registry_service = model_registry_service
        self.pipeline_service = pipeline_service
        self.drift_service = drift_service

    def summary(self) -> dict:
        readiness, _ = self.health_service.ready()
        active_model = None
        try:
            model = self.model_registry_service.get_active_model()
            active_model = {
                "model_name": model["model_name"],
                "model_version": model["model_version"],
                "stage": model["stage"],
            }
        except Exception:
            active_model = None

        latest_drift = self.drift_service.latest()

        return {
            "service": self.settings.app_name,
            "version": self.settings.app_version,
            "services": readiness["dependencies"],
            "active_model": active_model,
            "latest_pipeline_status": self.pipeline_service.latest_status(),
            "latest_drift_status": latest_drift["overall_status"],
            "timestamp": to_iso8601(utc_now()),
        }

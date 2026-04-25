from app.schemas.base import APIModel


class OpsSummaryResponse(APIModel):
    service: str
    version: str
    services: dict[str, str]
    active_model: dict[str, str] | None = None
    latest_pipeline_status: str
    latest_drift_status: str
    timestamp: str

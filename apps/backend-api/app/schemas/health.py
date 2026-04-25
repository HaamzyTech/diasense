from app.schemas.base import APIModel


class HealthResponse(APIModel):
    status: str
    service: str
    version: str
    timestamp: str


class ReadyResponse(HealthResponse):
    dependencies: dict[str, str]

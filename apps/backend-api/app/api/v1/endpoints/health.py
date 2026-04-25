from fastapi import APIRouter, Response, status

from app.api.deps import db_session_scope, get_health_service
from app.schemas.health import HealthResponse, ReadyResponse
from app.services.health_service import HealthService

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    with db_session_scope() as db:
        service: HealthService = get_health_service(db)
        return HealthResponse(**service.health())


@router.get("/ready", response_model=ReadyResponse)
async def get_ready(response: Response) -> ReadyResponse:
    with db_session_scope() as db:
        service: HealthService = get_health_service(db)
        payload, is_ready = service.ready()
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadyResponse(**payload)

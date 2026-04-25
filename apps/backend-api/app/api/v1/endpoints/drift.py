from fastapi import APIRouter

from app.api.deps import db_session_scope, get_drift_service
from app.schemas.drift import DriftResponse
from app.services.drift_service import DriftService

router = APIRouter(prefix="/drift")


@router.get("/latest", response_model=DriftResponse)
async def get_latest_drift() -> DriftResponse:
    with db_session_scope() as db:
        service: DriftService = get_drift_service(db)
        return DriftResponse(**service.latest())

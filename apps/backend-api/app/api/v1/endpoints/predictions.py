from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import db_session_scope, get_prediction_service
from app.schemas.predict import PredictionDetailResponse, PredictionListResponse
from app.services.prediction_service import PredictionService

router = APIRouter(prefix="/predictions")


@router.get("/{request_id}", response_model=PredictionDetailResponse)
async def get_prediction(request_id: UUID) -> PredictionDetailResponse:
    with db_session_scope() as db:
        service: PredictionService = get_prediction_service(db)
        return PredictionDetailResponse(**service.get_prediction(request_id))


@router.get("", response_model=PredictionListResponse)
async def list_predictions(
    session_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
) -> PredictionListResponse:
    with db_session_scope() as db:
        service: PredictionService = get_prediction_service(db)
        return PredictionListResponse(**service.list_predictions(session_id=session_id, limit=limit))

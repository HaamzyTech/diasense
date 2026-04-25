from fastapi import APIRouter

from app.api.deps import db_session_scope, get_prediction_service
from app.schemas.predict import MyPredictionsRequest, PredictionListResponse
from app.services.prediction_service import PredictionService

router = APIRouter()


@router.post("/my-predictions", response_model=PredictionListResponse)
async def my_predictions(payload: MyPredictionsRequest) -> PredictionListResponse:
    with db_session_scope() as db:
        service: PredictionService = get_prediction_service(db)
        return PredictionListResponse(**service.list_predictions(session_id=payload.session_id, limit=payload.limit))

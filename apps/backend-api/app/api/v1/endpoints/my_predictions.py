from fastapi import APIRouter, Request

from app.api.deps import db_session_scope, get_prediction_service, require_current_user
from app.schemas.predict import MyPredictionsRequest, PredictionListResponse
from app.services.prediction_service import PredictionService

router = APIRouter()


@router.post("/my-predictions", response_model=PredictionListResponse)
async def my_predictions(request: Request, payload: MyPredictionsRequest) -> PredictionListResponse:
    with db_session_scope() as db:
        current_user = require_current_user(db, request)
        service: PredictionService = get_prediction_service(db)
        return PredictionListResponse(**service.list_my_predictions(current_user=current_user, limit=payload.limit))

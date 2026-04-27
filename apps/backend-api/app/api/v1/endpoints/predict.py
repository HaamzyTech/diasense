from fastapi import APIRouter, Request

from app.api.deps import db_session_scope, get_prediction_service, require_current_user
from app.schemas.predict import PredictRequest, PredictResponse
from app.services.prediction_service import PredictionService

router = APIRouter()


@router.post("/predict", response_model=PredictResponse)
async def predict(request: Request, payload: PredictRequest) -> PredictResponse:
    with db_session_scope() as db:
        current_user = require_current_user(db, request)
        service: PredictionService = get_prediction_service(db)
        result = service.create_prediction(payload.model_dump(mode="json"), current_user=current_user)
        return PredictResponse(**result)

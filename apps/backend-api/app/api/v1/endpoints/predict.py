from fastapi import APIRouter

from app.api.deps import db_session_scope, get_prediction_service
from app.schemas.predict import PredictRequest, PredictResponse
from app.services.prediction_service import PredictionService

router = APIRouter()


@router.post("/predict", response_model=PredictResponse)
async def predict(payload: PredictRequest) -> PredictResponse:
    with db_session_scope() as db:
        service: PredictionService = get_prediction_service(db)
        result = service.create_prediction(payload.model_dump(mode="json"))
        return PredictResponse(**result)

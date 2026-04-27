from uuid import UUID

from fastapi import APIRouter, Query, Request

from app.api.deps import db_session_scope, get_prediction_service, require_current_user
from app.schemas.predict import DeletePredictionResponse, PredictionDetailResponse, PredictionListResponse
from app.services.prediction_service import PredictionService

router = APIRouter(prefix="/predictions")


@router.get("/{request_id}", response_model=PredictionDetailResponse)
async def get_prediction(request: Request, request_id: UUID) -> PredictionDetailResponse:
    with db_session_scope() as db:
        current_user = require_current_user(db, request)
        service: PredictionService = get_prediction_service(db)
        return PredictionDetailResponse(**service.get_prediction(request_id, current_user=current_user))


@router.get("", response_model=PredictionListResponse)
async def list_predictions(
    request: Request,
    patient_email: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> PredictionListResponse:
    with db_session_scope() as db:
        current_user = require_current_user(db, request)
        service: PredictionService = get_prediction_service(db)
        return PredictionListResponse(
            **service.list_predictions(
                current_user=current_user,
                patient_email=patient_email,
                limit=limit,
            )
        )


@router.delete("/{request_id}", response_model=DeletePredictionResponse)
async def delete_prediction(request: Request, request_id: UUID) -> DeletePredictionResponse:
    with db_session_scope() as db:
        current_user = require_current_user(db, request)
        service: PredictionService = get_prediction_service(db)
        return DeletePredictionResponse(
            **service.delete_prediction(request_id=request_id, current_user=current_user)
        )

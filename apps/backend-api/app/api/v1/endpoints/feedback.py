from fastapi import APIRouter, status

from app.api.deps import db_session_scope, get_feedback_service
from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.services.feedback_service import FeedbackService

router = APIRouter()


@router.post("/feedback", status_code=status.HTTP_201_CREATED, response_model=FeedbackResponse)
async def create_feedback(payload: FeedbackRequest) -> FeedbackResponse:
    with db_session_scope() as db:
        service: FeedbackService = get_feedback_service(db)
        row = service.create_feedback(payload.model_dump(mode="json"))
        return FeedbackResponse(**row)

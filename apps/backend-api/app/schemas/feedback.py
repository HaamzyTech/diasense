from uuid import UUID

from app.schemas.base import APIModel


class FeedbackRequest(APIModel):
    request_id: UUID
    ground_truth_label: bool
    label_source: str = "manual"
    notes: str | None = None


class FeedbackResponse(APIModel):
    message: str
    feedback_id: UUID
    request_id: UUID

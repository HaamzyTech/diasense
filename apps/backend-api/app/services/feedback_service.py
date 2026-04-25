from app.core.exceptions import NotFoundError
from app.repositories.feedback_repository import FeedbackRepository
from app.repositories.prediction_repository import PredictionRepository


class FeedbackService:
    def __init__(self, feedback_repo: FeedbackRepository, prediction_repo: PredictionRepository) -> None:
        self.feedback_repo = feedback_repo
        self.prediction_repo = prediction_repo

    def create_feedback(self, payload: dict) -> dict:
        if not self.prediction_repo.request_exists(payload["request_id"]):
            raise NotFoundError(f"Prediction request {payload['request_id']} not found")
        row = self.feedback_repo.create_feedback(payload)
        return {
            "message": "Feedback recorded",
            "feedback_id": row["id"],
            "request_id": row["request_id"],
        }

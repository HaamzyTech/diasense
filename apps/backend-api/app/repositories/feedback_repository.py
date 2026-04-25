from sqlalchemy import text
from sqlalchemy.orm import Session


class FeedbackRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_feedback(self, payload: dict) -> dict:
        stmt = text(
            """
            INSERT INTO feedback_labels (request_id, ground_truth_label, label_source, notes)
            VALUES (:request_id, :ground_truth_label, :label_source, :notes)
            RETURNING id, request_id
            """
        )
        row = self.db.execute(stmt, payload).mappings().one()
        self.db.commit()
        return dict(row)

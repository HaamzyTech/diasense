import json
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


class PredictionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_request(self, payload: dict) -> dict:
        stmt = text(
            """
            INSERT INTO prediction_requests (
                session_id,
                submitted_by,
                patient_email,
                actor_role,
                pregnancies,
                glucose,
                blood_pressure,
                skin_thickness,
                insulin,
                bmi,
                diabetes_pedigree_function,
                age,
                source
            ) VALUES (
                :session_id,
                :submitted_by,
                :patient_email,
                :actor_role,
                :pregnancies,
                :glucose,
                :blood_pressure,
                :skin_thickness,
                :insulin,
                :bmi,
                :diabetes_pedigree_function,
                :age,
                :source
            )
            RETURNING
                id,
                session_id,
                submitted_by,
                patient_email,
                actor_role,
                pregnancies,
                glucose,
                blood_pressure,
                skin_thickness,
                insulin,
                bmi,
                diabetes_pedigree_function,
                age,
                source,
                created_at
            """
        )
        row = self.db.execute(stmt, payload).mappings().one()
        self.db.commit()
        return dict(row)

    def create_result(self, payload: dict) -> dict:
        stmt = text(
            """
            INSERT INTO prediction_results (
                request_id,
                model_version_id,
                predicted_label,
                risk_probability,
                risk_band,
                explanation,
                latency_ms
            ) VALUES (
                :request_id,
                :model_version_id,
                :predicted_label,
                :risk_probability,
                :risk_band,
                CAST(:explanation AS jsonb),
                :latency_ms
            )
            RETURNING
                id,
                request_id,
                model_version_id,
                predicted_label,
                risk_probability,
                risk_band,
                explanation,
                latency_ms,
                created_at
            """
        )
        serializable_payload = dict(payload)
        serializable_payload["explanation"] = json.dumps(payload["explanation"])
        row = self.db.execute(stmt, serializable_payload).mappings().one()
        self.db.commit()
        return dict(row)

    def request_exists(self, request_id: UUID) -> bool:
        stmt = text("SELECT 1 FROM prediction_requests WHERE id = :request_id")
        row = self.db.execute(stmt, {"request_id": str(request_id)}).first()
        return row is not None

    def get_prediction(self, request_id: UUID) -> dict | None:
        stmt = text(
            """
            SELECT
                pr.id,
                pr.session_id,
                pr.submitted_by,
                pr.patient_email,
                pr.actor_role,
                pr.pregnancies,
                pr.glucose,
                pr.blood_pressure,
                pr.skin_thickness,
                pr.insulin,
                pr.bmi,
                pr.diabetes_pedigree_function,
                pr.age,
                pr.source,
                pr.created_at,
                res.id AS result_id,
                res.model_version_id,
                res.predicted_label,
                res.risk_probability,
                res.risk_band,
                res.explanation,
                res.latency_ms,
                res.created_at AS result_created_at
            FROM prediction_requests pr
            LEFT JOIN prediction_results res ON pr.id = res.request_id
            WHERE pr.id = :request_id
            """
        )
        row = self.db.execute(stmt, {"request_id": str(request_id)}).mappings().first()
        return dict(row) if row else None

    def list_predictions(self, limit: int, patient_email: str | None = None) -> list[dict]:
        query = """
            SELECT
                pr.id AS request_id,
                pr.submitted_by,
                pr.patient_email,
                pr.actor_role,
                res.risk_probability,
                res.risk_band,
                res.predicted_label,
                res.explanation,
                res.created_at
            FROM prediction_requests pr
            JOIN prediction_results res ON pr.id = res.request_id
        """
        params: dict[str, object] = {"limit": limit}
        if patient_email is not None:
            query += " WHERE pr.patient_email = :patient_email"
            params["patient_email"] = patient_email
        query += " ORDER BY res.created_at DESC LIMIT :limit"
        stmt = text(query)
        rows = self.db.execute(stmt, params).mappings().all()
        return [dict(row) for row in rows]

    def delete_prediction_request(self, request_id: UUID | str) -> dict | None:
        stmt = text(
            """
            DELETE FROM prediction_requests
            WHERE id = :request_id
            RETURNING id, patient_email, submitted_by, actor_role, created_at
            """
        )
        row = self.db.execute(stmt, {"request_id": str(request_id)}).mappings().first()
        self.db.commit()
        return dict(row) if row else None

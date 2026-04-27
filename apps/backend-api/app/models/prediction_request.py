import uuid

from sqlalchemy import CheckConstraint, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PredictionRequest(Base):
    __tablename__ = "prediction_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    submitted_by: Mapped[str] = mapped_column(String(255), nullable=False)
    patient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_role: Mapped[str] = mapped_column(String(20), nullable=False)
    pregnancies: Mapped[int] = mapped_column(Integer, nullable=False)
    glucose: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    blood_pressure: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    skin_thickness: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    insulin: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    bmi: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    diabetes_pedigree_function: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(30), nullable=False, server_default=text("'web'"))
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    __table_args__ = (
        CheckConstraint("pregnancies >= 0 AND pregnancies <= 30", name="ck_prediction_requests_pregnancies"),
        CheckConstraint("glucose >= 0 AND glucose <= 300", name="ck_prediction_requests_glucose"),
        CheckConstraint("blood_pressure >= 0 AND blood_pressure <= 200", name="ck_prediction_requests_blood_pressure"),
        CheckConstraint("skin_thickness >= 0 AND skin_thickness <= 100", name="ck_prediction_requests_skin_thickness"),
        CheckConstraint("insulin >= 0 AND insulin <= 1000", name="ck_prediction_requests_insulin"),
        CheckConstraint("bmi >= 0 AND bmi <= 100", name="ck_prediction_requests_bmi"),
        CheckConstraint(
            "diabetes_pedigree_function >= 0 AND diabetes_pedigree_function <= 10",
            name="ck_prediction_requests_dpf",
        ),
        CheckConstraint("age >= 1 AND age <= 120", name="ck_prediction_requests_age"),
    )

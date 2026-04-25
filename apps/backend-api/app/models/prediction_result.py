import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PredictionResult(Base):
    __tablename__ = "prediction_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("prediction_requests.id", ondelete="CASCADE"), nullable=False, unique=True)
    model_version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("model_versions.id"), nullable=False)
    predicted_label: Mapped[bool] = mapped_column(nullable=False)
    risk_probability: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    risk_band: Mapped[str] = mapped_column(String(20), nullable=False)
    explanation: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    __table_args__ = (
        CheckConstraint("risk_probability >= 0 AND risk_probability <= 1", name="ck_prediction_results_risk_probability"),
        CheckConstraint("latency_ms >= 0", name="ck_prediction_results_latency_ms"),
    )

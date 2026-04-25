import uuid

from sqlalchemy import Date, Float, String, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DriftReport(Base):
    __tablename__ = "drift_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    pipeline_run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    feature_name: Mapped[str] = mapped_column(String(100), nullable=False)
    baseline_mean: Mapped[float] = mapped_column(Float, nullable=False)
    current_mean: Mapped[float] = mapped_column(Float, nullable=False)
    baseline_variance: Mapped[float] = mapped_column(Float, nullable=False)
    current_variance: Mapped[float] = mapped_column(Float, nullable=False)
    psi: Mapped[float | None] = mapped_column(Float, nullable=True)
    ks_stat: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    report_date: Mapped[str] = mapped_column(Date, nullable=False, server_default=text("CURRENT_DATE"))
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

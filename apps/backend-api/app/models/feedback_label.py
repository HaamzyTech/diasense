import uuid

from sqlalchemy import ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FeedbackLabel(Base):
    __tablename__ = "feedback_labels"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("prediction_requests.id", ondelete="CASCADE"), nullable=False)
    ground_truth_label: Mapped[bool] = mapped_column(nullable=False)
    label_source: Mapped[str] = mapped_column(String(50), nullable=False, server_default=text("'manual'"))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

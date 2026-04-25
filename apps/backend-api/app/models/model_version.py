import uuid

from sqlalchemy import Boolean, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, server_default=text("'diasense-diabetes-risk'"))
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    mlflow_run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    mlflow_model_uri: Mapped[str] = mapped_column(Text, nullable=False)
    algorithm: Mapped[str] = mapped_column(String(100), nullable=False)
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    params: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    stage: Mapped[str] = mapped_column(String(30), nullable=False, server_default=text("'staging'"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

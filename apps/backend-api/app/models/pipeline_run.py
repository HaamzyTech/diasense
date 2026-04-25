import uuid

from sqlalchemy import Integer, String, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    pipeline_name: Mapped[str] = mapped_column(String(100), nullable=False)
    airflow_dag_id: Mapped[str] = mapped_column(String(100), nullable=False)
    airflow_run_id: Mapped[str] = mapped_column(String(100), nullable=False)
    git_commit_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    dvc_rev: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mlflow_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    started_at: Mapped[str | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    ended_at: Mapped[str | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-04-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
    op.execute("CREATE TYPE actor_role AS ENUM ('patient', 'clinician', 'admin');")
    op.execute("CREATE TYPE pipeline_status AS ENUM ('queued', 'running', 'success', 'failed');")
    op.execute("CREATE TYPE risk_band AS ENUM ('low', 'moderate', 'high');")

    op.create_table(
        "model_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("model_name", sa.String(length=100), nullable=False, server_default=sa.text("'diasense-diabetes-risk'")),
        sa.Column("model_version", sa.String(length=50), nullable=False),
        sa.Column("mlflow_run_id", sa.String(length=64), nullable=False),
        sa.Column("mlflow_model_uri", sa.Text(), nullable=False),
        sa.Column("algorithm", sa.String(length=100), nullable=False),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("params", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("stage", sa.String(length=30), nullable=False, server_default=sa.text("'staging'")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "prediction_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_role", postgresql.ENUM(name="actor_role", create_type=False), nullable=False),
        sa.Column("pregnancies", sa.Integer(), nullable=False),
        sa.Column("glucose", sa.Numeric(6, 2), nullable=False),
        sa.Column("blood_pressure", sa.Numeric(6, 2), nullable=False),
        sa.Column("skin_thickness", sa.Numeric(6, 2), nullable=False),
        sa.Column("insulin", sa.Numeric(8, 2), nullable=False),
        sa.Column("bmi", sa.Numeric(6, 2), nullable=False),
        sa.Column("diabetes_pedigree_function", sa.Numeric(8, 4), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=30), nullable=False, server_default=sa.text("'web'")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("pregnancies >= 0 AND pregnancies <= 30"),
        sa.CheckConstraint("glucose >= 0 AND glucose <= 300"),
        sa.CheckConstraint("blood_pressure >= 0 AND blood_pressure <= 200"),
        sa.CheckConstraint("skin_thickness >= 0 AND skin_thickness <= 100"),
        sa.CheckConstraint("insulin >= 0 AND insulin <= 1000"),
        sa.CheckConstraint("bmi >= 0 AND bmi <= 100"),
        sa.CheckConstraint("diabetes_pedigree_function >= 0 AND diabetes_pedigree_function <= 10"),
        sa.CheckConstraint("age >= 1 AND age <= 120"),
    )

    op.create_table(
        "prediction_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("prediction_requests.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("model_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("model_versions.id"), nullable=False),
        sa.Column("predicted_label", sa.Boolean(), nullable=False),
        sa.Column("risk_probability", sa.Numeric(5, 4), nullable=False),
        sa.Column("risk_band", postgresql.ENUM(name="risk_band", create_type=False), nullable=False),
        sa.Column("explanation", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("risk_probability >= 0 AND risk_probability <= 1"),
        sa.CheckConstraint("latency_ms >= 0"),
    )

    op.create_table(
        "feedback_labels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("prediction_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ground_truth_label", sa.Boolean(), nullable=False),
        sa.Column("label_source", sa.String(length=50), nullable=False, server_default=sa.text("'manual'")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "drift_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("pipeline_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("feature_name", sa.String(length=100), nullable=False),
        sa.Column("baseline_mean", sa.Float(), nullable=False),
        sa.Column("current_mean", sa.Float(), nullable=False),
        sa.Column("baseline_variance", sa.Float(), nullable=False),
        sa.Column("current_variance", sa.Float(), nullable=False),
        sa.Column("psi", sa.Float(), nullable=True),
        sa.Column("ks_stat", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False, server_default=sa.text("CURRENT_DATE")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "pipeline_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("pipeline_name", sa.String(length=100), nullable=False),
        sa.Column("airflow_dag_id", sa.String(length=100), nullable=False),
        sa.Column("airflow_run_id", sa.String(length=100), nullable=False),
        sa.Column("git_commit_hash", sa.String(length=64), nullable=True),
        sa.Column("dvc_rev", sa.String(length=64), nullable=True),
        sa.Column("mlflow_run_id", sa.String(length=64), nullable=True),
        sa.Column("status", postgresql.ENUM(name="pipeline_status", create_type=False), nullable=False),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("ended_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "system_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("service_name", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_index("ix_prediction_requests_session_id", "prediction_requests", ["session_id"])
    op.create_index("ix_prediction_requests_created_at", "prediction_requests", ["created_at"])
    op.create_index("ix_prediction_results_model_version_id", "prediction_results", ["model_version_id"])
    op.create_index("ix_feedback_labels_request_id", "feedback_labels", ["request_id"])
    op.create_index("ix_drift_reports_report_date", "drift_reports", ["report_date"])
    op.create_index("ix_pipeline_runs_status", "pipeline_runs", ["status"])
    op.create_index("ix_pipeline_runs_created_at", "pipeline_runs", ["created_at"])
    op.create_index("ix_system_events_service_name_created_at", "system_events", ["service_name", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_system_events_service_name_created_at", table_name="system_events")
    op.drop_index("ix_pipeline_runs_created_at", table_name="pipeline_runs")
    op.drop_index("ix_pipeline_runs_status", table_name="pipeline_runs")
    op.drop_index("ix_drift_reports_report_date", table_name="drift_reports")
    op.drop_index("ix_feedback_labels_request_id", table_name="feedback_labels")
    op.drop_index("ix_prediction_results_model_version_id", table_name="prediction_results")
    op.drop_index("ix_prediction_requests_created_at", table_name="prediction_requests")
    op.drop_index("ix_prediction_requests_session_id", table_name="prediction_requests")

    op.drop_table("system_events")
    op.drop_table("pipeline_runs")
    op.drop_table("drift_reports")
    op.drop_table("feedback_labels")
    op.drop_table("prediction_results")
    op.drop_table("prediction_requests")
    op.drop_table("model_versions")

    op.execute("DROP TYPE risk_band;")
    op.execute("DROP TYPE pipeline_status;")
    op.execute("DROP TYPE actor_role;")

"""add prediction ownership columns

Revision ID: 0003_prediction_ownership
Revises: 0002_auth_users
Create Date: 2026-04-26
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_prediction_ownership"
down_revision = "0002_auth_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("prediction_requests", sa.Column("submitted_by", sa.String(length=255), nullable=True))
    op.add_column("prediction_requests", sa.Column("patient_email", sa.String(length=255), nullable=True))

    op.execute(
        """
        UPDATE prediction_requests
        SET submitted_by = 'legacy-session',
            patient_email = 'legacy+' || session_id::text || '@diasense.local'
        WHERE submitted_by IS NULL OR patient_email IS NULL
        """
    )

    op.alter_column("prediction_requests", "submitted_by", nullable=False)
    op.alter_column("prediction_requests", "patient_email", nullable=False)
    op.create_index(
        "ix_prediction_requests_patient_email_created_at",
        "prediction_requests",
        ["patient_email", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_prediction_requests_submitted_by_created_at",
        "prediction_requests",
        ["submitted_by", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_prediction_requests_submitted_by_created_at", table_name="prediction_requests")
    op.drop_index("ix_prediction_requests_patient_email_created_at", table_name="prediction_requests")
    op.drop_column("prediction_requests", "patient_email")
    op.drop_column("prediction_requests", "submitted_by")

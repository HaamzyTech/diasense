"""add auth usernames

Revision ID: 0004_auth_usernames
Revises: 0003_prediction_ownership
Create Date: 2026-04-26
"""

from __future__ import annotations

import re

from alembic import op
import sqlalchemy as sa

revision = "0004_auth_usernames"
down_revision = "0003_prediction_ownership"
branch_labels = None
depends_on = None

USERNAME_ALLOWED = re.compile(r"[^a-z0-9._-]+")


def _normalize_username(candidate: str | None) -> str:
    normalized = (candidate or "").strip().lower()
    normalized = normalized.split("@", maxsplit=1)[0]
    normalized = USERNAME_ALLOWED.sub("-", normalized)
    normalized = normalized.strip("._-")
    return normalized or "user"


def upgrade() -> None:
    op.add_column("auth_users", sa.Column("username", sa.String(length=50), nullable=True))

    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            """
            SELECT id, email
            FROM auth_users
            ORDER BY created_at ASC, id ASC
            """
        )
    ).mappings()

    used_usernames: set[str] = set()
    for row in rows:
        base_username = _normalize_username(row["email"])
        username = base_username
        suffix = 2
        while username in used_usernames:
            username = f"{base_username}-{suffix}"
            suffix += 1
        used_usernames.add(username)
        connection.execute(
            sa.text("UPDATE auth_users SET username = :username WHERE id = :user_id"),
            {"username": username, "user_id": row["id"]},
        )

    op.alter_column("auth_users", "username", nullable=False)
    op.create_index("ix_auth_users_username", "auth_users", ["username"], unique=True)
    op.alter_column("auth_users", "email", existing_type=sa.String(length=255), nullable=True)


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            UPDATE auth_users
            SET email = CONCAT(username, '@diasense.local')
            WHERE email IS NULL
            """
        )
    )

    op.alter_column("auth_users", "email", existing_type=sa.String(length=255), nullable=False)
    op.drop_index("ix_auth_users_username", table_name="auth_users")
    op.drop_column("auth_users", "username")

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


class AuthUserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_user(
        self,
        username: str,
        email: str | None,
        password_hash: str,
        role: str = "patient",
    ) -> dict:
        stmt = text(
            """
            INSERT INTO auth_users (username, email, password_hash, role)
            VALUES (:username, :email, :password_hash, :role)
            RETURNING id, username, email, role, created_at
            """
        )
        row = self.db.execute(
            stmt,
            {
                "username": username,
                "email": email,
                "password_hash": password_hash,
                "role": role,
            },
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def get_by_email(self, email: str) -> dict | None:
        stmt = text(
            """
            SELECT id, username, email, password_hash, role, created_at
            FROM auth_users
            WHERE email = :email
            LIMIT 1
            """
        )
        row = self.db.execute(stmt, {"email": email}).mappings().first()
        return dict(row) if row else None

    def get_by_username(self, username: str) -> dict | None:
        stmt = text(
            """
            SELECT id, username, email, password_hash, role, created_at
            FROM auth_users
            WHERE username = :username
            LIMIT 1
            """
        )
        row = self.db.execute(stmt, {"username": username}).mappings().first()
        return dict(row) if row else None

    def get_by_identifier(self, identifier: str) -> dict | None:
        user = self.get_by_username(identifier)
        if user is not None:
            return user
        return self.get_by_email(identifier)

    def get_by_id(self, user_id: UUID | str) -> dict | None:
        stmt = text(
            """
            SELECT id, username, email, password_hash, role, created_at
            FROM auth_users
            WHERE id = :user_id
            LIMIT 1
            """
        )
        row = self.db.execute(stmt, {"user_id": str(user_id)}).mappings().first()
        return dict(row) if row else None

    def list_users(self, limit: int = 200) -> list[dict]:
        stmt = text(
            """
            SELECT id, username, email, role, created_at
            FROM auth_users
            ORDER BY created_at DESC, COALESCE(email, username) ASC
            LIMIT :limit
            """
        )
        rows = self.db.execute(stmt, {"limit": limit}).mappings().all()
        return [dict(row) for row in rows]

    def update_role(self, user_id: UUID | str, role: str) -> dict | None:
        stmt = text(
            """
            UPDATE auth_users
            SET role = :role
            WHERE id = :user_id
            RETURNING id, username, email, role, created_at
            """
        )
        row = self.db.execute(
            stmt,
            {
                "user_id": str(user_id),
                "role": role,
            },
        ).mappings().first()
        self.db.commit()
        return dict(row) if row else None

    def delete_user(self, user_id: UUID | str) -> dict | None:
        stmt = text(
            """
            DELETE FROM auth_users
            WHERE id = :user_id
            RETURNING id, username, email, role, created_at
            """
        )
        row = self.db.execute(stmt, {"user_id": str(user_id)}).mappings().first()
        self.db.commit()
        return dict(row) if row else None

    def list_patient_summaries(self, limit: int = 200) -> list[dict]:
        stmt = text(
            """
            SELECT
                u.id,
                u.username,
                u.email,
                u.role,
                u.created_at,
                COALESCE(stats.assessment_count, 0) AS assessment_count,
                stats.last_assessed_at,
                latest.latest_risk_band,
                latest.latest_risk_probability
            FROM auth_users u
            LEFT JOIN (
                SELECT
                    patient_email,
                    COUNT(*) AS assessment_count,
                    MAX(created_at) AS last_assessed_at
                FROM prediction_requests
                GROUP BY patient_email
            ) stats ON stats.patient_email = COALESCE(u.email, u.username)
            LEFT JOIN LATERAL (
                SELECT
                    res.risk_band AS latest_risk_band,
                    res.risk_probability AS latest_risk_probability
                FROM prediction_requests pr
                JOIN prediction_results res ON res.request_id = pr.id
                WHERE pr.patient_email = COALESCE(u.email, u.username)
                ORDER BY res.created_at DESC
                LIMIT 1
            ) latest ON TRUE
            ORDER BY COALESCE(stats.last_assessed_at, u.created_at) DESC, COALESCE(u.email, u.username) ASC
            LIMIT :limit
            """
        )
        rows = self.db.execute(stmt, {"limit": limit}).mappings().all()
        return [dict(row) for row in rows]

    def update_password(self, user_id: UUID | str, password_hash: str) -> None:
        stmt = text(
            """
            UPDATE auth_users
            SET password_hash = :password_hash
            WHERE id = :user_id
            """
        )
        self.db.execute(stmt, {"user_id": str(user_id), "password_hash": password_hash})
        self.db.commit()

from sqlalchemy import text
from sqlalchemy.orm import Session


class AuthUserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_user(self, email: str, password_hash: str, role: str = "patient") -> dict:
        stmt = text(
            """
            INSERT INTO auth_users (email, password_hash, role)
            VALUES (:email, :password_hash, :role)
            RETURNING id, email, role, created_at
            """
        )
        row = self.db.execute(
            stmt,
            {
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
            SELECT id, email, password_hash, role, created_at
            FROM auth_users
            WHERE email = :email
            LIMIT 1
            """
        )
        row = self.db.execute(stmt, {"email": email}).mappings().first()
        return dict(row) if row else None

    def update_password(self, email: str, password_hash: str) -> None:
        stmt = text(
            """
            UPDATE auth_users
            SET password_hash = :password_hash
            WHERE email = :email
            """
        )
        self.db.execute(stmt, {"email": email, "password_hash": password_hash})
        self.db.commit()

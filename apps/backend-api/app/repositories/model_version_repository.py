from sqlalchemy import text
from sqlalchemy.orm import Session


class ModelVersionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_active(self) -> dict | None:
        stmt = text(
            """
            SELECT
                id,
                model_name,
                model_version,
                mlflow_run_id,
                mlflow_model_uri,
                algorithm,
                metrics,
                params,
                stage,
                is_active,
                created_at
            FROM model_versions
            WHERE is_active = TRUE
            ORDER BY created_at DESC
            LIMIT 1
            """
        )
        row = self.db.execute(stmt).mappings().first()
        return dict(row) if row else None

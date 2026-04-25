from sqlalchemy import text
from sqlalchemy.orm import Session


class PipelineRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def count_runs(self) -> int:
        stmt = text("SELECT COUNT(*) AS count FROM pipeline_runs")
        row = self.db.execute(stmt).mappings().one()
        return int(row["count"])

    def list_runs(self, limit: int) -> list[dict]:
        stmt = text(
            """
            SELECT id, pipeline_name, airflow_dag_id, airflow_run_id, status, mlflow_run_id,
                   started_at, ended_at, duration_seconds
            FROM pipeline_runs
            ORDER BY created_at DESC
            LIMIT :limit
            """
        )
        rows = self.db.execute(stmt, {"limit": limit}).mappings().all()
        return [dict(row) for row in rows]

    def latest_status(self) -> str:
        stmt = text("SELECT status FROM pipeline_runs ORDER BY created_at DESC LIMIT 1")
        row = self.db.execute(stmt).mappings().first()
        return str(row["status"]) if row else "unknown"

    def latest_run(self) -> dict | None:
        stmt = text(
            """
            SELECT id, pipeline_name, airflow_dag_id, airflow_run_id, status, mlflow_run_id,
                   started_at, ended_at, duration_seconds
            FROM pipeline_runs
            ORDER BY created_at DESC
            LIMIT 1
            """
        )
        row = self.db.execute(stmt).mappings().first()
        return dict(row) if row else None

from app.schemas.base import APIModel


class PipelineRunItem(APIModel):
    id: str | None = None
    pipeline_name: str
    airflow_dag_id: str
    airflow_run_id: str
    status: str
    mlflow_run_id: str | None = None
    started_at: str | None = None
    ended_at: str | None = None
    duration_seconds: int | None = None


class PipelineRunsResponse(APIModel):
    items: list[PipelineRunItem]
    count: int

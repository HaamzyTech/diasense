from app.schemas.base import APIModel


class ModelInfoResponse(APIModel):
    model_name: str
    model_version: str
    algorithm: str
    stage: str
    mlflow_run_id: str
    mlflow_model_uri: str
    metrics: dict[str, float | int | str | bool]
    params: dict[str, float | int | str | bool]
    created_at: str | None = None

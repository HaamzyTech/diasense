import os


def resolve_tracking_uri(configured_uri: str | None) -> str | None:
    env_uri = os.getenv("MLFLOW_TRACKING_URI")
    if env_uri:
        return env_uri
    return configured_uri


def resolve_experiment_name(mlflow_config: dict[str, str | None] | None) -> str:
    if not mlflow_config:
        return "diabetes_risk_predictor"

    experiment_name = (
        mlflow_config.get("experiment_name")
        or mlflow_config.get("expreiment_name")
        or "diabetes_risk_predictor"
    )
    return str(experiment_name)

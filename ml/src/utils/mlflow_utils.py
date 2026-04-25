import json
from numbers import Real
from pathlib import Path
from typing import Any, Iterable

from utils.runtime import resolve_experiment_name, resolve_tracking_uri


def import_mlflow():
    try:
        import mlflow
    except ImportError as e:
        raise ImportError(
            "MLflow is not installed. Install it with: pip install mlflow"
        ) from e
    return mlflow


def configure_mlflow(mlflow_config: dict[str, Any]):
    mlflow = import_mlflow()
    tracking_uri = resolve_tracking_uri(mlflow_config.get("tracking_uri"))
    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)

    experiment_name = resolve_experiment_name(mlflow_config)
    mlflow.set_experiment(experiment_name)
    return mlflow, tracking_uri, experiment_name


def flatten_dict(data: dict[str, Any], parent_key: str = "") -> dict[str, Any]:
    items: dict[str, Any] = {}
    for key, value in data.items():
        new_key = f"{parent_key}.{key}" if parent_key else str(key)
        if isinstance(value, dict):
            items.update(flatten_dict(value, new_key))
        elif isinstance(value, list):
            items[new_key] = json.dumps(value)
        else:
            items[new_key] = value
    return items


def log_flattened_entries(mlflow, data: dict[str, Any], prefix: str) -> None:
    flattened = flatten_dict(data, prefix)
    params: dict[str, str] = {}

    for key, value in flattened.items():
        if isinstance(value, bool):
            mlflow.log_metric(key, float(value))
        elif isinstance(value, Real):
            mlflow.log_metric(key, float(value))
        elif value is not None:
            params[key] = str(value)

    if params:
        mlflow.log_params(params)


def log_artifacts(mlflow, artifact_paths: Iterable[Path], artifact_path: str) -> None:
    for path in artifact_paths:
        if path.exists():
            mlflow.log_artifact(str(path), artifact_path=artifact_path)

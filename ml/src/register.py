import json
import os
import time
from pathlib import Path
from typing import Any

from config import ROOT
from utils.io import ensure_dirs, parse_args, read_params, save_json
from utils.metrics import metric_optional_value
from utils.runtime import resolve_experiment_name, resolve_tracking_uri


def import_mlflow_dependencies():
    try:
        import mlflow
        from mlflow.tracking import MlflowClient
    except ImportError as e:
        raise ImportError(
            "MLflow is not installed. Install it with: pip install mlflow"
        ) from e
    return mlflow, MlflowClient


def import_psycopg2_dependencies():
    try:
        import psycopg2
        from psycopg2.extras import Json
    except ImportError as e:
        raise ImportError(
            "psycopg2-binary is not installed. Install it with: pip install psycopg2-binary"
        ) from e
    return psycopg2, Json


def pipeline_db_connect(psycopg2_module):
    dsn = os.getenv("DIASENSE_PIPELINE_DB_DSN", "").strip()
    if dsn:
        return psycopg2_module.connect(dsn)

    return psycopg2_module.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "diasense"),
        user=os.getenv("POSTGRES_USER", "diasense"),
        password=os.getenv("POSTGRES_PASSWORD", "diasense"),
    )


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def resolve_selected_result(evaluation_summary: dict[str, Any]) -> dict[str, Any]:
    serving_candidate = evaluation_summary.get("serving_candidate", {})
    selected_model_name = str(
        serving_candidate.get("model_name")
        or evaluation_summary.get("best_model_name")
        or ""
    )
    if not selected_model_name:
        raise ValueError("Evaluation summary does not include a selected serving candidate.")

    for result in evaluation_summary.get("results", []):
        if str(result.get("model_name")) == selected_model_name:
            return result

    raise ValueError(
        f"Selected serving candidate {selected_model_name!r} is missing from evaluation results."
    )


def find_existing_model_version(client, registered_model_name: str, source_run_id: str | None):
    if not source_run_id:
        return None

    try:
        versions = client.search_model_versions(f"name='{registered_model_name}'")
    except Exception:
        return None

    for version in versions:
        if str(getattr(version, "run_id", "")) == str(source_run_id):
            return version
    return None


def wait_for_model_version_ready(
    client,
    registered_model_name: str,
    version: str,
    timeout_seconds: int = 120,
):
    deadline = time.time() + timeout_seconds
    last_status = ""

    while time.time() < deadline:
        model_version = client.get_model_version(
            name=registered_model_name,
            version=version,
        )
        status = str(getattr(model_version, "status", ""))
        normalized_status = status.upper()

        if normalized_status.endswith("READY") or not normalized_status:
            return model_version
        if normalized_status.endswith("FAILED_REGISTRATION"):
            raise RuntimeError(
                f"Model version {registered_model_name} v{version} failed registration."
            )

        last_status = status
        time.sleep(2)

    raise TimeoutError(
        "Timed out waiting for registered model "
        f"{registered_model_name} v{version} to become READY. Last status: {last_status}"
    )


def register_selected_model(
    mlflow,
    client,
    selected_result: dict[str, Any],
    mlflow_params: dict[str, Any],
    primary_metric: str,
) -> dict[str, Any]:
    registered_model_name = str(
        mlflow_params.get("registered_model_name", "diasense-diabetes-risk")
    )
    serving_stage = str(mlflow_params.get("serving_model_stage", "Production"))
    archive_existing_versions = bool(
        mlflow_params.get("archive_existing_versions", True)
    )

    if not bool(selected_result.get("thresholds", {}).get("passed")):
        raise RuntimeError(
            "Selected serving candidate did not pass thresholds and cannot be registered."
        )

    existing_version = find_existing_model_version(
        client,
        registered_model_name,
        selected_result.get("source_run_id"),
    )

    if existing_version is None:
        registration = mlflow.register_model(
            selected_result["model_uri"],
            registered_model_name,
        )
        version = str(getattr(registration, "version", "")).strip()
        if not version:
            raise RuntimeError(
                f"MLflow did not return a model version for {registered_model_name}."
            )
        model_version = wait_for_model_version_ready(client, registered_model_name, version)
    else:
        model_version = existing_version
        version = str(getattr(model_version, "version", "")).strip()
        if not version:
            raise RuntimeError(
                f"Existing MLflow model version for {registered_model_name} is missing a version id."
            )

    client.transition_model_version_stage(
        name=registered_model_name,
        version=version,
        stage=serving_stage,
        archive_existing_versions=archive_existing_versions,
    )
    client.set_model_version_tag(
        name=registered_model_name,
        version=version,
        key="selected_for_serving",
        value="true",
    )
    client.set_model_version_tag(
        name=registered_model_name,
        version=version,
        key="selection_metric",
        value=primary_metric,
    )
    client.set_model_version_tag(
        name=registered_model_name,
        version=version,
        key="evaluation_run_id",
        value=str(selected_result["evaluation_run_id"]),
    )
    client.set_model_version_tag(
        name=registered_model_name,
        version=version,
        key="thresholds_passed",
        value=str(bool(selected_result["thresholds"]["passed"])).lower(),
    )

    return {
        "registered_model_name": registered_model_name,
        "registered_model_version": version,
        "serving_model_stage": serving_stage,
        "source_run_id": str(getattr(model_version, "run_id", "")) or str(selected_result.get("source_run_id", "")),
        "evaluation_run_id": str(selected_result["evaluation_run_id"]),
        "primary_metric": primary_metric,
        "primary_metric_value": metric_optional_value(
            selected_result["test_metrics"],
            primary_metric,
        ),
        "thresholds_passed": bool(selected_result["thresholds"]["passed"]),
        "mlflow_model_uri": f"models:/{registered_model_name}/{version}",
        "mlflow_stage_model_uri": f"models:/{registered_model_name}/{serving_stage}",
    }


def build_model_version_record(
    params: dict[str, Any],
    evaluation_summary: dict[str, Any],
    selected_result: dict[str, Any],
    serving_model: dict[str, Any],
) -> dict[str, Any]:
    algorithm = str(evaluation_summary.get("best_model_name", selected_result["model_name"]))
    model_name = str(serving_model["registered_model_name"])
    model_version = str(serving_model["registered_model_version"])
    model_stage = str(serving_model.get("serving_model_stage", "Production")).lower()

    return {
        "model_name": model_name,
        "model_version": model_version,
        "mlflow_run_id": serving_model.get("source_run_id"),
        "mlflow_model_uri": serving_model["mlflow_model_uri"],
        "algorithm": algorithm,
        "metrics": selected_result.get("test_metrics", {}),
        "params": params.get("train", {}).get("models", {}).get(algorithm, {}),
        "stage": model_stage,
        "is_active": True,
    }


def upsert_model_version_record(
    params: dict[str, Any],
    evaluation_summary: dict[str, Any],
    selected_result: dict[str, Any],
    serving_model: dict[str, Any],
) -> dict[str, Any]:
    psycopg2, Json = import_psycopg2_dependencies()
    record = build_model_version_record(
        params=params,
        evaluation_summary=evaluation_summary,
        selected_result=selected_result,
        serving_model=serving_model,
    )

    conn = pipeline_db_connect(psycopg2)
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE model_versions SET is_active = FALSE WHERE model_name = %s",
                    (record["model_name"],),
                )
                cursor.execute(
                    """
                    SELECT id
                    FROM model_versions
                    WHERE model_name = %s AND model_version = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (record["model_name"], record["model_version"]),
                )
                existing = cursor.fetchone()

                if existing:
                    cursor.execute(
                        """
                        UPDATE model_versions
                        SET
                            mlflow_run_id = %s,
                            mlflow_model_uri = %s,
                            algorithm = %s,
                            metrics = %s,
                            params = %s,
                            stage = %s,
                            is_active = TRUE
                        WHERE id = %s
                        """,
                        (
                            record["mlflow_run_id"],
                            record["mlflow_model_uri"],
                            record["algorithm"],
                            Json(record["metrics"]),
                            Json(record["params"]),
                            record["stage"],
                            existing[0],
                        ),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO model_versions
                            (
                                model_name,
                                model_version,
                                mlflow_run_id,
                                mlflow_model_uri,
                                algorithm,
                                metrics,
                                params,
                                stage,
                                is_active
                            )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE)
                        """,
                        (
                            record["model_name"],
                            record["model_version"],
                            record["mlflow_run_id"],
                            record["mlflow_model_uri"],
                            record["algorithm"],
                            Json(record["metrics"]),
                            Json(record["params"]),
                            record["stage"],
                        ),
                    )
    finally:
        conn.close()

    return record


def build_registration_summary(
    evaluation_summary: dict[str, Any],
    serving_model: dict[str, Any],
    selected_result: dict[str, Any],
    tracking_uri: str | None,
    experiment_name: str,
) -> dict[str, Any]:
    return {
        "parent_run_id": evaluation_summary.get("parent_run_id"),
        "tracking_uri": tracking_uri,
        "experiment_name": experiment_name,
        "primary_metric": evaluation_summary.get("primary_metric"),
        "best_model_name": evaluation_summary.get("best_model_name"),
        "best_model_uri": evaluation_summary.get("best_model_uri"),
        "serving_candidate": evaluation_summary.get("serving_candidate", {}),
        "serving_model": serving_model,
        "selected_result": selected_result,
    }


def main():
    args = parse_args()
    params = read_params(Path(ROOT / args.config))
    ensure_dirs(params)

    file_params = params["files"]
    path_params = params["paths"]
    mlflow_params = params["mlflow"]

    reports_dir = ROOT / path_params["ARTIFACTS_DIR"] / path_params["report_dir"]
    evaluation_summary_path = reports_dir / file_params["evaluation_summary"]
    if not evaluation_summary_path.exists():
        raise FileNotFoundError(
            f"Evaluation summary not found at {evaluation_summary_path}."
        )

    evaluation_summary = load_json(evaluation_summary_path)
    selected_result = resolve_selected_result(evaluation_summary)
    primary_metric = str(evaluation_summary.get("primary_metric", params["train"]["primary_metric"]))

    mlflow, MlflowClient = import_mlflow_dependencies()
    tracking_uri = resolve_tracking_uri(mlflow_params.get("tracking_uri"))
    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)
    experiment_name = resolve_experiment_name(mlflow_params)
    mlflow.set_experiment(experiment_name)
    client = MlflowClient()

    serving_model = register_selected_model(
        mlflow=mlflow,
        client=client,
        selected_result=selected_result,
        mlflow_params=mlflow_params,
        primary_metric=primary_metric,
    )
    model_version_record = upsert_model_version_record(
        params=params,
        evaluation_summary=evaluation_summary,
        selected_result=selected_result,
        serving_model=serving_model,
    )

    registration_summary = build_registration_summary(
        evaluation_summary=evaluation_summary,
        serving_model=serving_model,
        selected_result=selected_result,
        tracking_uri=tracking_uri,
        experiment_name=experiment_name,
    )
    registration_summary["model_version_record"] = model_version_record

    registration_summary_path = reports_dir / file_params["registration_summary"]
    save_json(registration_summary_path, registration_summary)

    print(
        "[OK] Registered serving model: "
        f"{serving_model['registered_model_name']} v{serving_model['registered_model_version']} "
        f"({serving_model['serving_model_stage']})"
    )
    print(f"[OK] Registration summary written to: {registration_summary_path}")


if __name__ == "__main__":
    main()

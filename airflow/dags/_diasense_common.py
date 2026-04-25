import json
import os
import subprocess
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import psycopg2
import yaml
from psycopg2.extras import Json


PIPELINE_FAILURE_STATES = {"failed", "upstream_failed"}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def repo_root() -> Path:
    return Path(os.getenv("DIASENSE_REPO_ROOT", "/workspace")).resolve()


def ml_dir() -> Path:
    default = repo_root() / "ml"
    return Path(os.getenv("DIASENSE_ML_DIR", str(default))).resolve()


def resolve_ml_path(raw_path: str | Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (ml_dir() / path).resolve()


def ml_config_path() -> Path:
    return resolve_ml_path(os.getenv("DIASENSE_ML_CONFIG_PATH", "params.yaml"))


def load_params() -> dict[str, Any]:
    with ml_config_path().open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def reports_dir(params: dict[str, Any]) -> Path:
    return (
        ml_dir()
        / params["paths"]["ARTIFACTS_DIR"]
        / params["paths"]["report_dir"]
    )


def baseline_dir(params: dict[str, Any]) -> Path:
    return (
        ml_dir()
        / params["paths"]["ARTIFACTS_DIR"]
        / params["paths"]["baseline_dir"]
    )


def current_feature_stats_path(params: dict[str, Any]) -> Path:
    default = reports_dir(params) / "current_feature_stats.json"
    return resolve_ml_path(os.getenv("DIASENSE_CURRENT_FEATURE_STATS_PATH", str(default)))


def drift_report_path(params: dict[str, Any]) -> Path:
    default = reports_dir(params) / "drift_report.json"
    return resolve_ml_path(os.getenv("DIASENSE_DRIFT_REPORT_PATH", str(default)))


def alert_metrics_path(params: dict[str, Any]) -> Path:
    default = reports_dir(params) / "drift_alert_metrics.prom"
    return resolve_ml_path(os.getenv("DIASENSE_ALERT_METRICS_PATH", str(default)))


def baseline_snapshot_path(params: dict[str, Any]) -> Path:
    default = baseline_dir(params) / params["files"]["drift_baseline"]
    return resolve_ml_path(os.getenv("DIASENSE_BASELINE_PATH", str(default)))


def baseline_data_path() -> Path:
    return resolve_ml_path(
        os.getenv("DIASENSE_BASELINE_DATA_PATH", "data/features/train.csv")
    )


def recent_data_path() -> Path:
    return resolve_ml_path(
        os.getenv("DIASENSE_RECENT_DATA_PATH", "data/processed/processed.csv")
    )


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)


def save_text(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")


def load_dataframe(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix == ".parquet":
        return pd.read_parquet(path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    raise ValueError(f"Unsupported dataframe format for {path}")


def ml_environment() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(ml_dir() / "src"))
    env.setdefault("MLFLOW_TRACKING_URI", "http://mlflow-tracking:5000")
    return env


def run_ml_script(script_name: str) -> None:
    subprocess.run(
        [sys.executable, f"src/{script_name}", "--config", str(ml_config_path())],
        cwd=str(ml_dir()),
        env=ml_environment(),
        check=True,
    )


def run_dvc_stage(stage_name: str) -> None:
    subprocess.run(
        ["dvc", "repro", stage_name],
        cwd=str(ml_dir()),
        env=ml_environment(),
        check=True,
    )


def git_commit_hash() -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root()), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    value = result.stdout.strip()
    return value or None


def dvc_revision() -> str | None:
    return git_commit_hash()


def pipeline_db_connect():
    dsn = os.getenv("DIASENSE_PIPELINE_DB_DSN", "").strip()
    if dsn:
        return psycopg2.connect(dsn)

    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "diasense"),
        user=os.getenv("POSTGRES_USER", "diasense"),
        password=os.getenv("POSTGRES_PASSWORD", "diasense"),
    )


@contextmanager
def pipeline_db_cursor():
    conn = pipeline_db_connect()
    try:
        with conn:
            with conn.cursor() as cursor:
                yield cursor
    finally:
        conn.close()


def ensure_pipeline_run_record(context: dict[str, Any], pipeline_name: str) -> str:
    dag_id = context["dag"].dag_id
    airflow_run_id = context["run_id"]
    started_at = context["dag_run"].start_date or utcnow()

    with pipeline_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT id
            FROM pipeline_runs
            WHERE airflow_dag_id = %s AND airflow_run_id = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (dag_id, airflow_run_id),
        )
        existing = cursor.fetchone()
        if existing:
            return str(existing[0])

        cursor.execute(
            """
            INSERT INTO pipeline_runs
                (
                    pipeline_name,
                    airflow_dag_id,
                    airflow_run_id,
                    git_commit_hash,
                    dvc_rev,
                    status,
                    started_at
                )
            VALUES (%s, %s, %s, %s, %s, %s::pipeline_status, %s)
            RETURNING id
            """,
            (
                pipeline_name,
                dag_id,
                airflow_run_id,
                git_commit_hash(),
                dvc_revision(),
                "running",
                started_at,
            ),
        )
        created = cursor.fetchone()
        if created is None:
            raise RuntimeError("Failed to create pipeline run record.")
        return str(created[0])


def infer_pipeline_status(context: dict[str, Any], final_task_id: str) -> str:
    dag_id = context["dag"].dag_id
    run_id = context["run_id"]

    with pipeline_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT task_id, state
            FROM task_instance
            WHERE dag_id = %s
              AND run_id = %s
              AND task_id <> %s
            """,
            (dag_id, run_id, final_task_id),
        )
        upstream_states = [state for _, state in cursor.fetchall()]

    if any(state in PIPELINE_FAILURE_STATES for state in upstream_states):
        return "failed"
    return "success"


def finalize_pipeline_run(
    context: dict[str, Any],
    pipeline_name: str,
    final_task_id: str,
    mlflow_run_id: str | None = None,
    status_override: str | None = None,
) -> str:
    pipeline_run_id = ensure_pipeline_run_record(context, pipeline_name)
    started_at = context["dag_run"].start_date or utcnow()
    ended_at = utcnow()
    duration_seconds = int((ended_at - started_at).total_seconds())
    status = status_override or infer_pipeline_status(context, final_task_id)

    with pipeline_db_cursor() as cursor:
        cursor.execute(
            """
            UPDATE pipeline_runs
            SET
                status = %s::pipeline_status,
                ended_at = %s,
                duration_seconds = %s,
                git_commit_hash = COALESCE(%s, git_commit_hash),
                dvc_rev = COALESCE(%s, dvc_rev),
                mlflow_run_id = COALESCE(%s, mlflow_run_id)
            WHERE id = %s
            """,
            (
                status,
                ended_at,
                duration_seconds,
                git_commit_hash(),
                dvc_revision(),
                mlflow_run_id,
                pipeline_run_id,
            ),
        )

    return status


def resolve_training_mlflow_run_id(params: dict[str, Any]) -> str | None:
    evaluation_path = reports_dir(params) / params["files"]["evaluation_summary"]
    if evaluation_path.exists():
        summary = load_json(evaluation_path)
        serving = summary.get("serving_model", {})
        return (
            serving.get("source_run_id")
            or serving.get("evaluation_run_id")
            or summary.get("parent_run_id")
        )

    train_summary_path = reports_dir(params) / params["files"]["train_summary"]
    if train_summary_path.exists():
        summary = load_json(train_summary_path)
        return summary.get("best_run_id") or summary.get("parent_run_id")

    return None


def update_model_registry_record(params: dict[str, Any]) -> dict[str, Any]:
    evaluation_path = reports_dir(params) / params["files"]["evaluation_summary"]
    if not evaluation_path.exists():
        raise FileNotFoundError(
            f"Evaluation summary not found at {evaluation_path}."
        )

    evaluation_summary = load_json(evaluation_path)
    serving_model = evaluation_summary.get("serving_model", {})
    registered_model_name = str(
        serving_model.get(
            "registered_model_name",
            params.get("mlflow", {}).get("registered_model_name", "diasense-diabetes-risk"),
        )
    )
    registered_model_version = str(serving_model["registered_model_version"])
    algorithm = str(evaluation_summary.get("best_model_name", "unknown"))
    model_uri = str(
        evaluation_summary.get(
            "best_model_uri",
            f"models:/{registered_model_name}/{serving_model.get('serving_model_stage', 'Production')}",
        )
    )
    metrics_payload: dict[str, Any] = {}
    for result in evaluation_summary.get("results", []):
        if str(result.get("model_name")) == algorithm:
            metrics_payload = result.get("test_metrics", {})
            break

    params_payload = (
        params.get("train", {})
        .get("models", {})
        .get(algorithm, {})
    )

    with pipeline_db_cursor() as cursor:
        cursor.execute(
            "UPDATE model_versions SET is_active = FALSE WHERE model_name = %s",
            (registered_model_name,),
        )
        cursor.execute(
            """
            SELECT id
            FROM model_versions
            WHERE model_name = %s AND model_version = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (registered_model_name, registered_model_version),
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
                    serving_model.get("source_run_id"),
                    model_uri,
                    algorithm,
                    Json(metrics_payload),
                    Json(params_payload),
                    str(serving_model.get("serving_model_stage", "Production")).lower(),
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
                    registered_model_name,
                    registered_model_version,
                    serving_model.get("source_run_id"),
                    model_uri,
                    algorithm,
                    Json(metrics_payload),
                    Json(params_payload),
                    str(serving_model.get("serving_model_stage", "Production")).lower(),
                ),
            )

    return {
        "registered_model_name": registered_model_name,
        "registered_model_version": registered_model_version,
        "algorithm": algorithm,
        "mlflow_run_id": serving_model.get("source_run_id"),
        "mlflow_model_uri": model_uri,
    }


def numeric_feature_columns(params: dict[str, Any]) -> list[str]:
    return list(params.get("schema", {}).get("feature_cols", []))


def clean_numeric_values(df: pd.DataFrame, feature_name: str) -> np.ndarray:
    if feature_name not in df.columns:
        return np.array([], dtype=float)
    values = pd.to_numeric(df[feature_name], errors="coerce")
    values = values.replace([np.inf, -np.inf], np.nan).dropna()
    return values.astype(float).to_numpy()


def compute_feature_stats(df: pd.DataFrame, feature_names: list[str]) -> dict[str, dict[str, Any]]:
    stats: dict[str, dict[str, Any]] = {}
    for feature_name in feature_names:
        values = clean_numeric_values(df, feature_name)
        stats[feature_name] = {
            "row_count": int(len(df)),
            "non_null_count": int(values.size),
            "null_count": int(len(df) - values.size),
            "mean": None if values.size == 0 else float(np.mean(values)),
            "variance": None if values.size == 0 else float(np.var(values)),
            "min": None if values.size == 0 else float(np.min(values)),
            "max": None if values.size == 0 else float(np.max(values)),
        }
    return stats


def compute_psi(baseline_values: np.ndarray, current_values: np.ndarray, buckets: int = 10) -> float | None:
    if baseline_values.size == 0 or current_values.size == 0:
        return None

    lower = float(min(np.min(baseline_values), np.min(current_values)))
    upper = float(max(np.max(baseline_values), np.max(current_values)))
    if np.isclose(lower, upper):
        return 0.0

    bin_edges = np.linspace(lower, upper, buckets + 1)
    baseline_hist, _ = np.histogram(baseline_values, bins=bin_edges)
    current_hist, _ = np.histogram(current_values, bins=bin_edges)

    epsilon = 1e-6
    baseline_dist = np.where(baseline_hist == 0, epsilon, baseline_hist.astype(float))
    current_dist = np.where(current_hist == 0, epsilon, current_hist.astype(float))

    baseline_dist = baseline_dist / baseline_dist.sum()
    current_dist = current_dist / current_dist.sum()

    return float(np.sum((current_dist - baseline_dist) * np.log(current_dist / baseline_dist)))


def compute_ks_statistic(baseline_values: np.ndarray, current_values: np.ndarray) -> float | None:
    if baseline_values.size == 0 or current_values.size == 0:
        return None

    baseline_sorted = np.sort(baseline_values)
    current_sorted = np.sort(current_values)
    combined = np.sort(np.concatenate([baseline_sorted, current_sorted]))

    baseline_cdf = np.searchsorted(baseline_sorted, combined, side="right") / baseline_sorted.size
    current_cdf = np.searchsorted(current_sorted, combined, side="right") / current_sorted.size
    return float(np.max(np.abs(baseline_cdf - current_cdf)))


def drift_thresholds() -> dict[str, float]:
    return {
        "psi": float(os.getenv("DIASENSE_DRIFT_PSI_THRESHOLD", "0.2")),
        "ks_stat": float(os.getenv("DIASENSE_DRIFT_KS_THRESHOLD", "0.2")),
        "mean_shift_stddevs": float(
            os.getenv("DIASENSE_DRIFT_MEAN_SHIFT_THRESHOLD", "1.0")
        ),
    }


def build_drift_report(params: dict[str, Any]) -> dict[str, Any]:
    feature_names = numeric_feature_columns(params)
    baseline_df = load_dataframe(baseline_data_path())
    current_df = load_dataframe(recent_data_path())

    baseline_stats = compute_feature_stats(baseline_df, feature_names)
    current_stats = compute_feature_stats(current_df, feature_names)
    thresholds = drift_thresholds()

    feature_reports: list[dict[str, Any]] = []
    drift_detected = False

    for feature_name in feature_names:
        baseline_values = clean_numeric_values(baseline_df, feature_name)
        current_values = clean_numeric_values(current_df, feature_name)
        baseline_feature_stats = baseline_stats[feature_name]
        current_feature_stats = current_stats[feature_name]

        baseline_variance = baseline_feature_stats["variance"]
        baseline_std = 0.0 if baseline_variance in (None, 0.0) else float(np.sqrt(baseline_variance))
        mean_shift = None
        if (
            baseline_feature_stats["mean"] is not None
            and current_feature_stats["mean"] is not None
        ):
            diff = abs(
                float(current_feature_stats["mean"]) - float(baseline_feature_stats["mean"])
            )
            mean_shift = float(diff if baseline_std == 0.0 else diff / baseline_std)

        psi = compute_psi(baseline_values, current_values)
        ks_stat = compute_ks_statistic(baseline_values, current_values)

        has_signal = any(
            (
                psi is not None and psi >= thresholds["psi"],
                ks_stat is not None and ks_stat >= thresholds["ks_stat"],
                mean_shift is not None and mean_shift >= thresholds["mean_shift_stddevs"],
            )
        )
        if baseline_values.size == 0 or current_values.size == 0:
            status = "insufficient_data"
        else:
            status = "drift" if has_signal else "ok"

        drift_detected = drift_detected or status == "drift"
        feature_reports.append(
            {
                "feature_name": feature_name,
                "baseline_mean": baseline_feature_stats["mean"],
                "current_mean": current_feature_stats["mean"],
                "baseline_variance": baseline_feature_stats["variance"],
                "current_variance": current_feature_stats["variance"],
                "psi": psi,
                "ks_stat": ks_stat,
                "mean_shift_stddevs": mean_shift,
                "status": status,
            }
        )

    baseline_payload = {
        "generated_at": utcnow().isoformat(),
        "source_path": str(baseline_data_path()),
        "feature_stats": baseline_stats,
    }
    save_json(baseline_snapshot_path(params), baseline_payload)

    return {
        "generated_at": utcnow().isoformat(),
        "pipeline_name": "diasense_monitoring_pipeline",
        "baseline_data_path": str(baseline_data_path()),
        "current_data_path": str(recent_data_path()),
        "thresholds": thresholds,
        "drift_detected": drift_detected,
        "features": feature_reports,
    }


def persist_drift_rows(
    pipeline_run_id: str,
    drift_report: dict[str, Any],
) -> None:
    with pipeline_db_cursor() as cursor:
        cursor.execute(
            "DELETE FROM drift_reports WHERE pipeline_run_id = %s",
            (pipeline_run_id,),
        )
        for feature in drift_report.get("features", []):
            cursor.execute(
                """
                INSERT INTO drift_reports
                    (
                        pipeline_run_id,
                        feature_name,
                        baseline_mean,
                        current_mean,
                        baseline_variance,
                        current_variance,
                        psi,
                        ks_stat,
                        status,
                        report_date
                    )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_DATE)
                """,
                (
                    pipeline_run_id,
                    feature["feature_name"],
                    feature.get("baseline_mean") or 0.0,
                    feature.get("current_mean") or 0.0,
                    feature.get("baseline_variance") or 0.0,
                    feature.get("current_variance") or 0.0,
                    feature.get("psi"),
                    feature.get("ks_stat"),
                    feature.get("status", "unknown"),
                ),
            )


def emit_system_events_for_drift(drift_report: dict[str, Any]) -> None:
    drifted_features = [
        feature["feature_name"]
        for feature in drift_report.get("features", [])
        if feature.get("status") == "drift"
    ]
    if not drifted_features:
        return

    with pipeline_db_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO system_events (service_name, severity, message, metadata)
            VALUES (%s, %s, %s, %s)
            """,
            (
                "airflow-monitoring",
                "warning",
                "Feature drift detected in monitoring pipeline.",
                Json(
                    {
                        "drifted_features": drifted_features,
                        "generated_at": drift_report.get("generated_at"),
                    }
                ),
            ),
        )

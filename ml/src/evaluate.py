
import json
import os
import time
from pathlib import Path
from typing import Any

from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

from config import ROOT
from utils.io import ensure_dirs, load_dataframe, parse_args, read_params, save_json
from utils.runtime import resolve_experiment_name, resolve_tracking_uri


def import_mlflow_dependencies():
    try:
        import mlflow
        import mlflow.sklearn
        from mlflow.models import evaluate as mlflow_evaluate
        from mlflow.tracking import MlflowClient
    except ImportError as e:
        raise ImportError(
            "MLflow is not installed. Install it with: pip install mlflow"
        ) from e
    return mlflow, mlflow_evaluate, MlflowClient

def resolve_candidates(ecfg: dict[str, Any]) -> list[dict[str, Any]]:
    if ecfg.get("model_uris"):
        return [
            {"model_name": item.get("model_name", f"model_{idx}"), "model_uri": item["model_uri"], "run_id": item.get("run_id")}
            for idx, item in enumerate(ecfg["model_uris"])
        ]

    train_summary_path_raw = ecfg.get("train_summary_path")
    if not train_summary_path_raw:
        raise ValueError("Provide evaluate.model_uris or evaluate.paths.train_summary_path")

    train_summary_path = Path(train_summary_path_raw)
    if not train_summary_path.exists():
        raise ValueError(f"Train summary file not found: {train_summary_path}")

    with open(train_summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    models = summary.get("models", [])
    if not models:
        raise ValueError("Train summary does not contain any candidate models.")
    return models


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


def promote_best_model_for_serving(
    mlflow,
    client,
    best_result: dict[str, Any],
    registered_model_name: str,
    serving_stage: str,
    archive_existing_versions: bool,
    primary_metric: str,
) -> dict[str, Any]:
    existing_version = find_existing_model_version(
        client,
        registered_model_name,
        best_result.get("source_run_id"),
    )

    if existing_version is None:
        registration = mlflow.register_model(best_result["model_uri"], registered_model_name)
        version = str(getattr(registration, "version"))
        model_version = wait_for_model_version_ready(client, registered_model_name, version)
    else:
        model_version = existing_version
        version = str(getattr(model_version, "version"))

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
        value=str(best_result["evaluation_run_id"]),
    )

    return {
        "registered_model_name": registered_model_name,
        "registered_model_version": version,
        "serving_model_stage": serving_stage,
        "source_run_id": str(getattr(model_version, "run_id", "")),
        "evaluation_run_id": str(best_result["evaluation_run_id"]),
        "primary_metric": primary_metric,
        "primary_metric_value": best_result["test_metrics"].get(primary_metric),
        "thresholds_passed": bool(best_result["thresholds"]["passed"]),
    }

def make_feature_frame(df: pd.DataFrame, target_column: str, drop_columns: list[str]) -> tuple[pd.DataFrame, pd.Series]:
    drop_set = set(drop_columns + [target_column])
    feature_columns = [c for c in df.columns if c not in drop_set]
    if not feature_columns:
        raise ValueError("No feature columns remain after dropping target and excluded columns.")
    X = df[feature_columns].copy()
    y = df[target_column].copy()
    return X, y



def predict_scores(model, X: pd.DataFrame) -> tuple[np.ndarray, np.ndarray | None]:
    y_pred = model.predict(X)
    y_prob: np.ndarray | None = None
    if hasattr(model, "predict_proba"):
        prob = model.predict_proba(X)
        if prob.ndim == 2 and prob.shape[1] >= 2:
            y_prob = prob[:, 1]
    elif hasattr(model, "decision_function"):
        scores = model.decision_function(X)
        if isinstance(scores, np.ndarray):
            y_prob = 1.0 / (1.0 + np.exp(-scores))
    return y_pred, y_prob



def compute_classification_metrics(y_true: pd.Series, y_pred: np.ndarray, y_prob: np.ndarray | None) -> dict[str, float]:
    metrics: dict[str, float] = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
    }
    if y_prob is not None:
        metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob))
        metrics["average_precision"] = float(average_precision_score(y_true, y_prob))
        metrics["log_loss"] = float(log_loss(y_true, np.column_stack([1.0 - y_prob, y_prob]), labels=[0, 1]))
    return metrics



def save_confusion_matrix_plot(y_true: pd.Series, y_pred: np.ndarray, filename: Path, title: str) -> None:
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(5, 4))
    image = ax.imshow(cm)
    plt.colorbar(image, ax=ax)
    ax.set_title(title)
    ax.set_xlabel("Predicted label")
    ax.set_ylabel("True label")
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center")
    fig.tight_layout()
    fig.savefig(filename, bbox_inches="tight")
    plt.close(fig)



def save_roc_curve_plot(y_true: pd.Series, y_prob: np.ndarray | None, filename: Path, title: str) -> None:
    if y_prob is None:
        return
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.plot(fpr, tpr)
    ax.plot([0, 1], [0, 1], linestyle="--")
    ax.set_title(title)
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    fig.tight_layout()
    fig.savefig(filename, bbox_inches="tight")
    plt.close(fig)

def save_precision_recall_curve_plot(y_true: pd.Series, y_prob: np.ndarray | None, filename: Path, title: str) -> None:
    if y_prob is None:
        return
    precision, recall, _ = precision_recall_curve(y_true, y_prob)
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.plot(recall, precision)
    ax.set_title(title)
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    fig.tight_layout()
    fig.savefig(filename, bbox_inches="tight")
    plt.close(fig)


def check_thresholds(metrics: dict[str, float], threshold_cfg: dict[str, Any]) -> dict[str, Any]:
    results: dict[str, Any] = {"passed": True, "checks": {}}
    minimums = threshold_cfg.get("minimums", {})
    maximums = threshold_cfg.get("maximums", {})

    for metric_name, threshold in minimums.items():
        value = metrics.get(metric_name)
        passed = value is not None and float(value) >= float(threshold)
        results["checks"][metric_name] = {
            "direction": "min",
            "threshold": float(threshold),
            "value": None if value is None else float(value),
            "passed": passed,
        }
        results["passed"] = results["passed"] and passed

    for metric_name, threshold in maximums.items():
        value = metrics.get(metric_name)
        passed = value is not None and float(value) <= float(threshold)
        results["checks"][metric_name] = {
            "direction": "max",
            "threshold": float(threshold),
            "value": None if value is None else float(value),
            "passed": passed,
        }
        results["passed"] = results["passed"] and passed

    return results

def metric_value(metrics: dict[str, float], metric_name: str) -> float:
    value = metrics.get(metric_name)
    if value is None:
        return float("-inf")
    return float(value)

def choose_best_evaluation(results: list[dict[str, Any]], primary_metric: str) -> dict[str, Any]:
    if primary_metric == "log_loss":
        ranked = sorted(results, key=lambda item: item["test_metrics"].get("log_loss", float("inf")))
        return ranked[0]
    ranked = sorted(results, key=lambda item: metric_value(item["test_metrics"], primary_metric), reverse=True)
    return ranked[0]


def choose_best_serving_candidate(
    results: list[dict[str, Any]],
    primary_metric: str,
) -> dict[str, Any]:
    eligible_results = [
        result for result in results if bool(result.get("thresholds", {}).get("passed"))
    ]
    if not eligible_results:
        raise RuntimeError(
            "No evaluated model passed the serving thresholds; refusing to select a model for serving."
        )
    return choose_best_evaluation(eligible_results, primary_metric)

def log_dataset_inputs(mlflow, from_pandas, run_df: pd.DataFrame, name: str) -> None:
    try:
        dataset = from_pandas(run_df, source=name)
        mlflow.log_input(dataset, context=name)
    except Exception:
        pass
    
def main():
    args = parse_args()
    params = read_params(Path(ROOT / args.config))
    ensure_dirs(params)

    ev_params = params["evaluate"]
    file_param = params["files"]
    path_param = params["paths"]
    mlflow_param = params["mlflow"]

    data_dir = path_param["DATA_DIR"]
    artifacts_dir = path_param["ARTIFACTS_DIR"]
    reports_dir = path_param["report_dir"]
    feature_dir = path_param["feature_data"]
    model_dir = path_param["model_dir"]

    test_data = file_param["test_set"]
    ev_summary = file_param["evaluation_summary"]
    label_col = params["schema"]["lable_col"]
    drop_columns = params["schema"]["drop_columns"]
    primary_metric = params["train"]["primary_metric"]
    registered_model_name = str(
        mlflow_param.get("registered_model_name", "diasense-diabetes-risk")
    )
    serving_model_stage = str(mlflow_param.get("serving_model_stage", "Production"))
    archive_existing_versions = bool(
        mlflow_param.get("archive_existing_versions", True)
    )

    candidate_paths = {
        "model_uris": ev_params.get("model_uris"),
        "train_summary_path": ROOT / artifacts_dir / reports_dir / file_param["train_summary"],
    }
    candidates = resolve_candidates(candidate_paths)

    mlflow, mlflow_evaluate, MlflowClient = import_mlflow_dependencies()

    tracking_uri = resolve_tracking_uri(mlflow_param.get("tracking_uri"))

    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)

    experiment_name = resolve_experiment_name(mlflow_param)
    mlflow.set_experiment(experiment_name)
    client = MlflowClient()

    while mlflow.active_run() is not None:
        mlflow.end_run()
    os.environ.pop("MLFLOW_RUN_ID", None)

    test_path = ROOT / data_dir / feature_dir / test_data
    test_df = load_dataframe(test_path)
    X_test, y_test = make_feature_frame(test_df, label_col, drop_columns)

    all_results: list[dict[str, Any]] = []

    with mlflow.start_run(run_name=mlflow_param.get("eval_run_name")) as parent_run:
        parent_run_id = parent_run.info.run_id
        mlflow.set_tags(
            {
                "stage": "evaluate_compare",
                "target_column": label_col,
                "primary_metric": primary_metric,
                "test_data_path": str(test_path),
            }
        )
        mlflow.log_params(
            {
                "candidate_count": len(candidates),
                "target_column": label_col,
                "test_rows": len(test_df),
                "primary_metric": primary_metric,
                "serving_registered_model_name": registered_model_name,
                "serving_model_stage": serving_model_stage,
            }
        )

        for candidate in candidates:
            model_name = str(candidate.get("model_name", "model"))
            model_uri = str(candidate["model_uri"])
            source_run_id = candidate.get("run_id")
            model = mlflow.sklearn.load_model(model_uri)

            y_pred, y_prob = predict_scores(model, X_test)
            test_metrics = compute_classification_metrics(y_test, y_pred, y_prob)
            threshold_results = check_thresholds(test_metrics, ev_params.get("thresholds", {}))
            report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

            predictions = X_test.copy()
            predictions[label_col] = y_test.values
            predictions["prediction"] = y_pred
            if y_prob is not None:
                predictions["prediction_probability"] = y_prob

            model_artifact_dir = ROOT / artifacts_dir / model_dir / model_name

            metrics_path = ROOT / artifacts_dir / reports_dir / file_param["test_metrics"]
            report_path = ROOT / artifacts_dir / reports_dir / file_param["test_classification_report"]
            thresholds_path = ROOT / artifacts_dir / reports_dir / file_param["threshold_results"]
            predictions_path = ROOT / artifacts_dir / reports_dir / file_param["test_predictions"]
            cm_path = ROOT / artifacts_dir / reports_dir / file_param["test_confusion_matrix"]
            roc_path = ROOT / artifacts_dir / reports_dir / file_param["test_roc_curve"]
            pr_path = ROOT / artifacts_dir / reports_dir / file_param["test_precision_recal_curve"]

            save_json(metrics_path, test_metrics)
            save_json(report_path, report)
            save_json(thresholds_path, threshold_results)
            predictions.to_csv(predictions_path, index=False)
            save_confusion_matrix_plot(y_test, y_pred, cm_path, f"{model_name} Test Confusion Matrix")
            save_roc_curve_plot(y_test, y_prob, roc_path, f"{model_name} Test ROC Curve")
            save_precision_recall_curve_plot(y_test, y_prob, pr_path, f"{model_name} Test PR Curve")

            with mlflow.start_run(run_name=f"evaluate_{model_name}", nested=True) as child_run:
                child_run_id = child_run.info.run_id
                mlflow.set_tags(
                    {
                        "stage": "evaluate_candidate",
                        "parent_run_id": parent_run_id,
                        "model_name": model_name,
                        "evaluated_model_uri": model_uri,
                        "source_train_run_id": "" if source_run_id is None else str(source_run_id),
                    }
                )
                mlflow.log_params(
                    {
                        "model_name": model_name,
                        "evaluated_model_uri": model_uri,
                    }
                )

                for metric_name, metric_value_item in test_metrics.items():
                    mlflow.log_metric(f"test_{metric_name}", metric_value_item)
                mlflow.log_metric("thresholds_passed", 1.0 if threshold_results["passed"] else 0.0)

                for artifact_file in [metrics_path, report_path, thresholds_path, predictions_path, cm_path, roc_path, pr_path]:
                    if artifact_file.exists():
                        mlflow.log_artifact(str(artifact_file), artifact_path=model_name)
            
                all_results.append(
                    {
                        "model_name": model_name,
                        "model_uri": model_uri,
                        "source_run_id": source_run_id,
                        "evaluation_run_id": child_run_id,
                        "test_metrics": test_metrics,
                        "thresholds": threshold_results,
                        "artifact_dir": str(model_artifact_dir),
                    }
                )

        best_result = choose_best_serving_candidate(all_results, primary_metric)
        evaluator_cfg = ev_params.get("mlflow_evaluator", {})
        if evaluator_cfg.get("enabled", False):
            best_model_artifact_dir = Path(best_result["artifact_dir"])
            try:
                with mlflow.start_run(
                    run_name=f"mlflow_evaluate_{best_result['model_name']}",
                    nested=True,
                ):
                    eval_data = X_test.copy()
                    eval_data[label_col] = y_test.values
                    mlflow_evaluate(
                        model=best_result["model_uri"],
                        data=eval_data,
                        targets=label_col,
                        model_type="classifier",
                        evaluators=["default"],
                        evaluator_config={
                            "log_explainer": bool(
                                evaluator_cfg.get("log_explainer", False)
                            ),
                        },
                    )
            except Exception as e:
                warning_path = best_model_artifact_dir / "mlflow_evaluate_warning.json"
                save_json(warning_path, {"warning": str(e)})
                mlflow.log_artifact(
                    str(warning_path),
                    artifact_path=best_result["model_name"],
                )

        serving_selection = promote_best_model_for_serving(
            mlflow=mlflow,
            client=client,
            best_result=best_result,
            registered_model_name=registered_model_name,
            serving_stage=serving_model_stage,
            archive_existing_versions=archive_existing_versions,
            primary_metric=primary_metric,
        )
        summary = {
            "parent_run_id": parent_run_id,
            "tracking_uri": tracking_uri,
            "experiment_name": experiment_name,
            "primary_metric": primary_metric,
            "best_model_name": best_result["model_name"],
            "best_model_uri": best_result["model_uri"],
            "serving_model": serving_selection,
            "results": all_results,
        }
        summary_path = ROOT / artifacts_dir / reports_dir / ev_summary
        save_json(summary_path, summary)
        mlflow.log_artifact(str(summary_path), artifact_path="comparison")
        mlflow.log_param("best_model_name", best_result["model_name"])
        mlflow.log_param("serving_registered_model_name", registered_model_name)
        mlflow.log_param("serving_model_stage", serving_model_stage)
        for metric_name, metric_value_item in best_result["test_metrics"].items():
            mlflow.log_metric(f"best_test_{metric_name}", metric_value_item)
        mlflow.set_tags(
            {
                "serving_registered_model_name": registered_model_name,
                "serving_registered_model_version": serving_selection["registered_model_version"],
                "serving_model_stage": serving_model_stage,
            }
        )

        print(f"[OK] Evaluated {len(all_results)} models.")
        print(f"[OK] Best test model by {primary_metric}: {best_result['model_name']}")
        print(
            "[OK] Selected serving model: "
            f"{registered_model_name} v{serving_selection['registered_model_version']} "
            f"({serving_model_stage})"
        )
        print(f"[OK] Evaluation summary written to: {summary_path}")


if __name__ == "__main__":
    main()

import json
import os
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
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
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from config import ROOT
from utils.runtime import resolve_experiment_name, resolve_tracking_uri
from utils.io import ensure_dirs, load_dataframe, parse_args, read_params, save_json, save_model


def import_mlflow_dependencies():
    try:
        import mlflow
        import mlflow.sklearn as mlflow_sklearn
        from mlflow.models import infer_signature
    except ImportError as e:
        raise ImportError(
            "MLflow is not installed. Install it with: pip install mlflow"
        ) from e
    return mlflow, mlflow_sklearn, infer_signature

def make_feature_frame(
    df: pd.DataFrame,
    target_column: str,
    drop_columns: list[str],
) -> tuple[pd.DataFrame, pd.Series]:
    drop_set = set(drop_columns + [target_column])
    feature_columns = [c for c in df.columns if c not in drop_set]
    if not feature_columns:
        raise ValueError("No feature columns remain after dropping target and excluded columns.")
    X = df[feature_columns].copy()
    y = df[target_column].copy()
    return X, y

def infer_column_types(
    X: pd.DataFrame,
    categorical_columns: list[str] | None,
) -> tuple[list[str], list[str]]:
    if categorical_columns:
        categorical = [c for c in categorical_columns if c in X.columns]
    else:
        categorical = [
            c for c in X.columns if X[c].dtype == "object" or str(X[c].dtype).startswith("category")
        ]
    numeric = [c for c in X.columns if c not in categorical]
    return numeric, categorical

def build_estimator(model_name: str, train_cfg: dict[str, Any], random_state: int):
    model_name = model_name.lower()
    model_cfg = train_cfg.get("models", {})

    if model_name == "logistic_regression":
        params = model_cfg.get("logistic_regression", {})
        return LogisticRegression(
            C=float(params.get("C", 1.0)),
            max_iter=int(params.get("max_iter", 1000)),
            solver=params.get("solver", "lbfgs"),
            class_weight=params.get("class_weight", None),
            random_state=random_state,
        )

    if model_name == "random_forest":
        params = model_cfg.get("random_forest", {})
        max_depth_raw = params.get("max_depth")
        max_depth = None if max_depth_raw in (None, "null", "None") else int(max_depth_raw)
        return RandomForestClassifier(
            n_estimators=int(params.get("n_estimators", 300)),
            max_depth=max_depth,
            min_samples_split=int(params.get("min_samples_split", 2)),
            min_samples_leaf=int(params.get("min_samples_leaf", 1)),
            class_weight=params.get("class_weight", None),
            random_state=random_state,
            n_jobs=int(params.get("n_jobs", -1)),
        )

    if model_name == "xgboost":
        try:
            from xgboost import XGBClassifier
        except ImportError as e:
            raise ImportError(
                "XGBoost is not installed. Install it with: pip install xgboost"
            ) from e

        params = model_cfg.get("xgboost", {})
        return XGBClassifier(
            n_estimators=int(params.get("n_estimators", 300)),
            max_depth=int(params.get("max_depth", 4)),
            learning_rate=float(params.get("learning_rate", 0.05)),
            subsample=float(params.get("subsample", 0.9)),
            colsample_bytree=float(params.get("colsample_bytree", 0.9)),
            min_child_weight=float(params.get("min_child_weight", 1.0)),
            reg_lambda=float(params.get("reg_lambda", 1.0)),
            objective="binary:logistic",
            eval_metric=str(params.get("eval_metric", "logloss")),
            random_state=random_state,
            n_jobs=int(params.get("n_jobs", -1)),
            tree_method=str(params.get("tree_method", "hist")),
        )

    raise ValueError(
        "Unsupported model. Expected one of: logistic_regression, random_forest, xgboost."
    )

def build_pipeline(
    X_train: pd.DataFrame,
    categorical_columns: list[str],
    numeric_columns: list[str],
    estimator,
) -> Pipeline:
    transformers = []

    if numeric_columns:
        transformers.append(
            (
                "num",
                Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))]),
                numeric_columns,
            )
        )

    if categorical_columns:
        transformers.append(
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        (
                            "encoder",
                            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                        ),
                    ]
                ),
                categorical_columns,
            )
        )

    if not transformers:
        raise ValueError("No usable feature columns were found for training.")

    preprocessor = ColumnTransformer(transformers=transformers, remainder="drop")
    return Pipeline(steps=[("features", preprocessor), ("model", estimator)])


def metric_value(metrics: dict[str, float], metric_name: str) -> float:
    value = metrics.get(metric_name)
    if value is None:
        return float("-inf")
    return float(value)

def compute_classification_metrics(
    y_true: pd.Series,
    y_pred: np.ndarray,
    y_prob: np.ndarray | None,
) -> dict[str, float]:
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

def predict_scores(model: Pipeline, X: pd.DataFrame) -> tuple[np.ndarray, np.ndarray | None]:
    pred_result = model.predict(X)
    # Handle case where predict returns a tuple
    y_pred = pred_result[0] if isinstance(pred_result, tuple) else pred_result
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

def choose_best_model(results: list[dict[str, Any]], primary_metric: str) -> dict[str, Any]:
    if primary_metric == "log_loss":
        ranked = sorted(results, key=lambda item: item["val_metrics"].get("log_loss", float("inf")))
        return ranked[0]
    ranked = sorted(
        results,
        key=lambda item: metric_value(item["val_metrics"], primary_metric),
        reverse=True,
    )
    return ranked[0]


def main():
    args = parse_args()
    params = read_params(Path(ROOT / args.config))

    ensure_dirs(params)
    random_state = int(params["data"]["random_state"])

    data_dir = params["paths"]["DATA_DIR"] 
    features_dir = params["paths"]["feature_data"]

    train_data = params["files"]["train_set"]
    val_data = params["files"]["val_set"]

    label_col = params["schema"]["lable_col"]

    artifacts_dir = params["paths"]["ARTIFACTS_DIR"]
    reports_dir = params["paths"]["report_dir"]
    model_dir = params["paths"]["model_dir"]

    best_model_file = params["files"]["best_model"]
    train_params = params["train"]

    categorical_columns_params = params["schema"]["categorical_columns"]
    drop_columns = params["schema"]["drop_columns"]
    primary_metric = params["train"]["primary_metric"]
    models_to_train = params["train"]["enabled_models"]

    mlflow, sklearn_mlflow, infer_signature = import_mlflow_dependencies()
    mlflow_params = params["mlflow"]
    tracking_uri = resolve_tracking_uri(mlflow_params.get("tracking_uri"))

    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)

    print("Tracking URI:", mlflow.get_tracking_uri())

    experiment_name = resolve_experiment_name(mlflow_params)
    mlflow.set_experiment(experiment_name)

    train_path = ROOT / data_dir / features_dir / train_data
    validation_path = ROOT / data_dir / features_dir / val_data
    train_df = load_dataframe(train_path)
    validation_df = load_dataframe(validation_path)

    X_train, y_train = make_feature_frame(train_df, label_col, drop_columns)
    X_val, y_val = make_feature_frame(validation_df, label_col, drop_columns)

    numeric_columns, categorical_columns = infer_column_types(X_train, categorical_columns_params)
    
    all_results: list[dict[str, Any]] = []

    while mlflow.active_run() is not None:
        mlflow.end_run()
    os.environ.pop("MLFLOW_RUN_ID", None)

    with mlflow.start_run(run_name=mlflow_params["train_run_name"]) as parent_run:
        parent_run_id = parent_run.info.run_id
        mlflow.set_tags({
            "stage": "train_compare",
            "target_column": label_col,
            "primary_metric": primary_metric,
            "train_data_path:": str(train_path),
            "validation_data_path": str(validation_path),
        })

        mlflow.log_params({
            "random_state": random_state,
            "target_column": label_col,
            "feature_count": X_train.shape[1],
            "train_rows": len(train_df),
            "validation_rows": len(validation_df),
            "enabled_models": json.dumps(models_to_train),
            "categorical_columns": json.dumps(categorical_columns),
            "numeric_columns": json.dumps(numeric_columns),
        })

        for model_name in models_to_train:
            estimator = build_estimator(model_name, train_params, random_state)
            pipeline = build_pipeline(X_train, categorical_columns, numeric_columns, estimator)
            pipeline.fit(X_train, y_train)

            train_pred, train_prob = predict_scores(pipeline, X_train)
            val_pred, val_prob = predict_scores(pipeline, X_val)

            train_metrics = compute_classification_metrics(y_train, train_pred, train_prob)
            val_metrics = compute_classification_metrics(y_val, val_pred, val_prob)

            train_report = classification_report(y_train, train_pred, output_dict=True, zero_division=0)
            val_report = classification_report(y_val, val_pred, output_dict=True, zero_division=0)
            # Ensure reports are dicts
            train_report = train_report if isinstance(train_report, dict) else {}
            val_report = val_report if isinstance(val_report, dict) else {}

            train_predictions = X_train.copy()
            train_predictions[label_col] = y_train.values
            train_predictions["prediction"] = train_pred
            if train_prob is not None:
                train_predictions["prediction_probability"] = train_prob

            val_predictions = X_val.copy()
            val_predictions[label_col] = y_val.values
            val_predictions["prediction"] = val_pred
            if val_prob is not None:
                val_predictions["prediction_probability"] = val_prob
            
            report_path = ROOT / artifacts_dir / reports_dir 
            file_p = params["files"]
            train_metrics_path =  report_path / file_p["train_metrics"]
            val_metrics_path = report_path / file_p["validation_metrics"]
            train_report_path = report_path / file_p["train_classification_report"]
            val_report_path = report_path / file_p["validation_classification_report"]
            train_pred_path = report_path / file_p["train_predictions"]
            val_pred_path = report_path / file_p["validation_predictions"]
            train_cnf_mat_path = report_path / file_p["train_confusion_matrix"]
            val_cnf_mat_path = report_path / file_p["validation_confusion_matrix"]
            val_roc_path = report_path / file_p["validation_roc_curve"]
            val_pr_path = report_path / file_p["validation_precision_recal_curve"]

            save_json(train_metrics_path, train_metrics)
            save_json(val_metrics_path, val_metrics)
            save_json(train_report_path, train_report)
            save_json(val_report_path, val_report)
            train_predictions.to_csv(train_pred_path, index=False)
            val_predictions.to_csv(val_pred_path, index=False)

            save_confusion_matrix_plot(y_train, train_pred, train_cnf_mat_path, f"{model_name} Train Confusion Matrix")
            save_confusion_matrix_plot(y_val, val_pred, val_cnf_mat_path, f"{model_name} Validation Confusion Matrix")
            save_roc_curve_plot(y_val, val_prob, val_roc_path, f"{model_name} Validation ROC Curve")
            save_precision_recall_curve_plot(y_val, val_prob, val_pr_path, f"{model_name} Validation PR Curve")

            
            with mlflow.start_run(run_name=f"{model_name}", nested=True) as child_run:
                child_run_id = child_run.info.run_id
                mlflow.set_tags(
                    {
                        "stage": "train_candidate",
                        "parent_run_id": parent_run_id,
                        "model_name": model_name,
                        "target_column": label_col,
                    }
                )
                mlflow.log_params(
                    {
                        "model_name": model_name,
                        "random_state": random_state,
                        "feature_count": X_train.shape[1],
                    }
                )
                mlflow.log_params(flatten_dict(train_params.get("models", {}).get(model_name, {}), f"model.{model_name}"))

                for metric_name, metric_value_item in train_metrics.items():
                    mlflow.log_metric(f"train_{metric_name}", metric_value_item)
                for metric_name, metric_value_item in val_metrics.items():
                    mlflow.log_metric(f"val_{metric_name}", metric_value_item)

                for artifact_file in [
                    train_metrics_path,
                    val_metrics_path,
                    train_report_path,
                    val_report_path,
                    train_pred_path,
                    val_pred_path,
                    train_cnf_mat_path,
                    val_cnf_mat_path,
                    val_roc_path,
                    val_pr_path,
                ]:
                    if artifact_file.exists():
                        mlflow.log_artifact(str(artifact_file), artifact_path=model_name)

                signature = infer_signature(X_train.head(20), pipeline.predict(X_train.head(20)))
                model_info = mlflow.sklearn.log_model(
                    sk_model=pipeline,
                    name="model",
                    signature=signature,
                    input_example=X_train.head(5),
                )

                model_uri = str(getattr(model_info, "model_uri", f"runs:/{child_run_id}/model"))
                result_record = {
                    "model_name": model_name,
                    "run_id": child_run_id,
                    "model_uri": model_uri,
                    "model_id": getattr(model_info, "model_id", None),
                    "train_metrics": train_metrics,
                    "val_metrics": val_metrics,
                    "artifact_dir": str(report_path),
                }
                all_results.append(result_record)

        best_result = choose_best_model(all_results, primary_metric)

        leaderboard = {
            "primary_metric": primary_metric,
            "ranked_models": sorted(
                all_results,
                key=(
                    (lambda item: item["val_metrics"].get("log_loss", float("inf")))
                    if primary_metric == "log_loss"
                    else (lambda item: metric_value(item["val_metrics"], primary_metric))
                ),
                reverse=primary_metric != "log_loss",
            ),
        }
        leaderboard_path = ROOT / artifacts_dir / reports_dir / params["files"]["leaderboard"]
        save_json(leaderboard_path, leaderboard)
        mlflow.log_artifact(str(leaderboard_path), artifact_path="comparison")

        summary = {
            "parent_run_id": parent_run_id,
            "tracking_uri": tracking_uri,
            "experiment_name": experiment_name,
            "primary_metric": primary_metric,
            "best_model_name": best_result["model_name"],
            "best_run_id": best_result["run_id"],
            "best_model_uri": best_result["model_uri"],
            "models": all_results,
        }
        summary_path = ROOT / artifacts_dir / reports_dir / params["files"]["train_summary"]
        save_json(summary_path, summary)
        mlflow.log_artifact(str(summary_path), artifact_path="comparison")

        mlflow.log_param("best_model_name", best_result["model_name"])
        for metric_name, metric_value_item in best_result["val_metrics"].items():
            mlflow.log_metric(f"best_val_{metric_name}", metric_value_item)

        registered_model_name = mlflow_params.get("registered_model_name")
        if registered_model_name:
            try:
                result = mlflow.register_model(best_result["model_uri"], str(registered_model_name))
                mlflow.set_tag("registered_model_name", str(registered_model_name))
                mlflow.set_tag("registered_model_version", str(getattr(result, "version", "")))
            except Exception:
                pass
        
        print(f"[OK] Trained {len(all_results)} models: {[item['model_name'] for item in all_results]}")
        print(f"[OK] Best model by {primary_metric}: {best_result['model_name']}")
        print(f"[OK] Train summary written to: {summary_path}") 


if __name__ == '__main__':
    main()

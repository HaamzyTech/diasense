from src.register import (
    build_model_version_record,
    build_registration_summary,
    register_selected_model,
    resolve_selected_result,
)


class DummyModelVersion:
    def __init__(self, version: str, run_id: str, status: str = "READY") -> None:
        self.version = version
        self.run_id = run_id
        self.status = status


class DummyClient:
    def __init__(self) -> None:
        self.transitions: list[tuple[str, str, str, bool]] = []
        self.tags: list[tuple[str, str, str, str]] = []
        self.model_versions = {
            ("diasense-diabetes-risk", "7"): DummyModelVersion(
                version="7",
                run_id="train-run-1",
            )
        }

    def search_model_versions(self, _query: str):
        return []

    def get_model_version(self, name: str, version: str):
        return self.model_versions[(name, version)]

    def transition_model_version_stage(
        self,
        name: str,
        version: str,
        stage: str,
        archive_existing_versions: bool,
    ) -> None:
        self.transitions.append((name, version, stage, archive_existing_versions))

    def set_model_version_tag(self, name: str, version: str, key: str, value: str) -> None:
        self.tags.append((name, version, key, value))


class DummyMlflow:
    def __init__(self) -> None:
        self.register_calls: list[tuple[str, str]] = []

    def register_model(self, model_uri: str, registered_model_name: str):
        self.register_calls.append((model_uri, registered_model_name))
        return DummyModelVersion(version="7", run_id="train-run-1")


def test_resolve_selected_result_uses_serving_candidate_name():
    summary = {
        "best_model_name": "random_forest",
        "serving_candidate": {"model_name": "logistic_regression"},
        "results": [
            {"model_name": "random_forest"},
            {"model_name": "logistic_regression", "model_uri": "models:/m-1"},
        ],
    }

    selected = resolve_selected_result(summary)

    assert selected["model_name"] == "logistic_regression"


def test_register_selected_model_registers_and_promotes_candidate():
    mlflow = DummyMlflow()
    client = DummyClient()
    selected_result = {
        "model_name": "logistic_regression",
        "model_uri": "models:/m-123",
        "source_run_id": "train-run-1",
        "evaluation_run_id": "eval-run-1",
        "thresholds": {"passed": True},
        "test_metrics": {"roc_auc": 0.88},
    }

    serving_model = register_selected_model(
        mlflow=mlflow,
        client=client,
        selected_result=selected_result,
        mlflow_params={
            "registered_model_name": "diasense-diabetes-risk",
            "serving_model_stage": "Production",
            "archive_existing_versions": True,
        },
        primary_metric="roc_auc",
    )

    assert mlflow.register_calls == [("models:/m-123", "diasense-diabetes-risk")]
    assert client.transitions == [("diasense-diabetes-risk", "7", "Production", True)]
    assert serving_model["registered_model_version"] == "7"
    assert serving_model["mlflow_model_uri"] == "models:/diasense-diabetes-risk/7"


def test_build_model_version_record_uses_registered_version_uri():
    params = {
        "train": {
            "models": {
                "logistic_regression": {"C": 1.0, "solver": "lbfgs"},
            }
        }
    }
    evaluation_summary = {"best_model_name": "logistic_regression"}
    selected_result = {
        "model_name": "logistic_regression",
        "test_metrics": {"accuracy": 0.78},
    }
    serving_model = {
        "registered_model_name": "diasense-diabetes-risk",
        "registered_model_version": "7",
        "serving_model_stage": "Production",
        "source_run_id": "train-run-1",
        "mlflow_model_uri": "models:/diasense-diabetes-risk/7",
    }

    record = build_model_version_record(
        params=params,
        evaluation_summary=evaluation_summary,
        selected_result=selected_result,
        serving_model=serving_model,
    )

    assert record["algorithm"] == "logistic_regression"
    assert record["mlflow_model_uri"] == "models:/diasense-diabetes-risk/7"
    assert record["metrics"] == {"accuracy": 0.78}
    assert record["params"] == {"C": 1.0, "solver": "lbfgs"}


def test_build_registration_summary_preserves_serving_model_details():
    summary = build_registration_summary(
        evaluation_summary={
            "parent_run_id": "parent-run-1",
            "primary_metric": "roc_auc",
            "best_model_name": "logistic_regression",
            "best_model_uri": "models:/m-123",
        },
        serving_model={
            "registered_model_name": "diasense-diabetes-risk",
            "registered_model_version": "7",
        },
        selected_result={"model_name": "logistic_regression"},
        tracking_uri="http://mlflow-tracking:5000",
        experiment_name="diabetes-risk-predictor_model",
    )

    assert summary["parent_run_id"] == "parent-run-1"
    assert summary["serving_model"]["registered_model_version"] == "7"
    assert summary["selected_result"]["model_name"] == "logistic_regression"

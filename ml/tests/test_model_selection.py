from src.evaluate import choose_best_serving_candidate
from src.train import choose_best_model, maybe_register_best_model


class DummyMlflow:
    def __init__(self) -> None:
        self.register_calls: list[tuple[str, str]] = []
        self.tags: dict[str, str] = {}

    def register_model(self, model_uri: str, registered_model_name: str):
        self.register_calls.append((model_uri, registered_model_name))
        return type("RegistrationResult", (), {"version": "7"})()

    def set_tag(self, key: str, value: str) -> None:
        self.tags[key] = value


def test_training_registration_is_disabled_by_default() -> None:
    mlflow = DummyMlflow()

    registered_name, registered_version = maybe_register_best_model(
        mlflow=mlflow,
        best_result={"model_uri": "models:/m-123"},
        registered_model_name="diasense-diabetes-risk",
        register_best_after_training=False,
    )

    assert registered_name is None
    assert registered_version is None
    assert mlflow.register_calls == []


def test_training_registration_runs_only_when_enabled() -> None:
    mlflow = DummyMlflow()

    registered_name, registered_version = maybe_register_best_model(
        mlflow=mlflow,
        best_result={"model_uri": "models:/m-123"},
        registered_model_name="diasense-diabetes-risk",
        register_best_after_training=True,
    )

    assert registered_name == "diasense-diabetes-risk"
    assert registered_version == "7"
    assert mlflow.register_calls == [("models:/m-123", "diasense-diabetes-risk")]
    assert mlflow.tags["registered_model_name"] == "diasense-diabetes-risk"
    assert mlflow.tags["registered_model_version"] == "7"


def test_choose_best_serving_candidate_requires_threshold_pass() -> None:
    best = choose_best_serving_candidate(
        [
            {
                "model_name": "random_forest",
                "test_metrics": {"roc_auc": 0.91},
                "thresholds": {"passed": False},
            },
            {
                "model_name": "logistic_regression",
                "test_metrics": {"roc_auc": 0.88},
                "thresholds": {"passed": True},
            },
        ],
        primary_metric="roc_auc",
    )

    assert best["model_name"] == "logistic_regression"


def test_choose_best_serving_candidate_raises_when_none_pass() -> None:
    try:
        choose_best_serving_candidate(
            [
                {
                    "model_name": "random_forest",
                    "test_metrics": {"roc_auc": 0.91},
                    "thresholds": {"passed": False},
                }
            ],
            primary_metric="roc_auc",
        )
    except RuntimeError as exc:
        assert "No evaluated model passed the serving thresholds" in str(exc)
    else:
        raise AssertionError("Expected choose_best_serving_candidate to raise")


def test_choose_best_serving_candidate_supports_prefixed_primary_metric() -> None:
    best = choose_best_serving_candidate(
        [
            {
                "model_name": "random_forest",
                "test_metrics": {"f1": 0.81},
                "thresholds": {"passed": True},
            },
            {
                "model_name": "logistic_regression",
                "test_metrics": {"f1": 0.84},
                "thresholds": {"passed": True},
            },
        ],
        primary_metric="val_f1",
    )

    assert best["model_name"] == "logistic_regression"


def test_choose_best_model_supports_prefixed_primary_metric() -> None:
    best = choose_best_model(
        [
            {
                "model_name": "random_forest",
                "val_metrics": {"f1": 0.81},
            },
            {
                "model_name": "logistic_regression",
                "val_metrics": {"f1": 0.84},
            },
        ],
        primary_metric="val_f1",
    )

    assert best["model_name"] == "logistic_regression"

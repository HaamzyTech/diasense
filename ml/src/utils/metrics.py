from typing import Any


KNOWN_METRIC_PREFIXES = ("train_", "val_", "validation_", "test_")


def metric_name_candidates(metric_name: str) -> list[str]:
    normalized = str(metric_name)
    candidates = [normalized]

    for prefix in KNOWN_METRIC_PREFIXES:
        if normalized.startswith(prefix):
            candidates.append(normalized[len(prefix):])

    unique_candidates: list[str] = []
    for candidate in candidates:
        if candidate not in unique_candidates:
            unique_candidates.append(candidate)
    return unique_candidates


def metric_optional_value(metrics: dict[str, Any], metric_name: str) -> float | None:
    for candidate in metric_name_candidates(metric_name):
        value = metrics.get(candidate)
        if value is not None:
            return float(value)
    return None

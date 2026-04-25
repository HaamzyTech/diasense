from fastapi import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, REGISTRY, generate_latest
from prometheus_client.core import CounterMetricFamily, GaugeMetricFamily

from app.db.session import SessionLocal
from app.repositories.drift_repository import DriftRepository
from app.repositories.pipeline_repository import PipelineRepository

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests handled by backend-api.",
    ["method", "path", "status_code"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method", "path"],
)
PREDICTION_REQUESTS_TOTAL = Counter(
    "prediction_requests_total",
    "Total prediction requests that completed successfully.",
    ["risk_band"],
)
PREDICTION_ERRORS_TOTAL = Counter(
    "prediction_errors_total",
    "Total prediction failures.",
    ["reason"],
)
MODEL_INFERENCE_LATENCY_MS = Gauge(
    "model_inference_latency_ms",
    "Latest model inference latency in milliseconds.",
)
BACKEND_API_EXCEPTIONS_TOTAL = Counter(
    "backend_api_exceptions_total",
    "Total backend-api exceptions by type.",
    ["exception_type"],
)


def collect_operational_metrics() -> tuple[float, float]:
    db = SessionLocal()
    try:
        pipeline_runs_total = float(PipelineRepository(db).count_runs())
        drift_detected = float(DriftRepository(db).latest_drift_detected())
        return pipeline_runs_total, drift_detected
    except Exception:
        return 0.0, 0.0
    finally:
        db.close()


class OperationalMetricsCollector:
    def collect(self):
        pipeline_runs_total, drift_detected = collect_operational_metrics()

        pipeline_runs_metric = CounterMetricFamily(
            "pipeline_runs_total",
            "Total pipeline runs recorded in the pipeline_runs table.",
        )
        pipeline_runs_metric.add_metric([], pipeline_runs_total)

        drift_detected_metric = GaugeMetricFamily(
            "drift_detected_gauge",
            "Whether the latest drift report indicates detected drift.",
        )
        drift_detected_metric.add_metric([], drift_detected)

        yield pipeline_runs_metric
        yield drift_detected_metric


try:
    REGISTRY.register(OperationalMetricsCollector())
except ValueError:
    pass


def metrics_response() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

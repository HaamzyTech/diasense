from fastapi import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

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


def metrics_response() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

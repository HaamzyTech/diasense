import httpx
import pytest

from app.main import app


@pytest.mark.anyio
async def test_metrics_endpoint_exposes_expected_metrics() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")

    body = response.text
    assert "http_requests_total" in body
    assert "http_request_duration_seconds" in body
    assert "prediction_requests_total" in body
    assert "prediction_errors_total" in body
    assert "model_inference_latency_ms" in body
    assert "pipeline_runs_total" in body
    assert "drift_detected_gauge" in body

import httpx
import pytest

from app.api.v1.endpoints import health
from app.main import app


@pytest.mark.anyio
async def test_health_endpoint() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "backend-api"
    assert body["version"] == "0.1.0"


@pytest.mark.anyio
async def test_ready_endpoint(monkeypatch) -> None:
    class DummyHealthService:
        def ready(self):
            return (
                {
                    "status": "ready",
                    "service": "backend-api",
                    "version": "0.1.0",
                    "dependencies": {
                        "postgres": "ok",
                        "model_server": "ok",
                        "mlflow_tracking": "ok",
                    },
                    "timestamp": "2026-04-25T10:00:00Z",
                },
                True,
            )

    monkeypatch.setattr(health, "get_health_service", lambda _db: DummyHealthService())

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["dependencies"]["postgres"] == "ok"
    assert body["dependencies"]["model_server"] == "ok"
    assert body["dependencies"]["mlflow_tracking"] == "ok"

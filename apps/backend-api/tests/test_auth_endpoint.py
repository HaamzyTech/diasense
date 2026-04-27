from contextlib import contextmanager

import httpx
import pytest

from app.api.v1.endpoints import auth
from app.main import app


class DummyAuthService:
    def signup(self, username: str | None, email: str | None, password: str) -> dict:
        assert username == "user123"
        assert email == "user@example.com"
        assert password == "securepass"
        return {
            "access_token": "signed-token",
            "token_type": "bearer",
            "expires_in": 43200,
            "user": {
                "username": "user123",
                "email": "user@example.com",
                "role": "patient",
                "auth_source": "database",
            },
        }


@contextmanager
def dummy_db_scope():
    yield object()


@pytest.mark.anyio
async def test_signup_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(auth, "db_session_scope", dummy_db_scope)
    monkeypatch.setattr(auth, "get_auth_service", lambda _db: DummyAuthService())

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/signup",
            json={
                "username": "user123",
                "email": "user@example.com",
                "password": "securepass",
            },
        )

    assert response.status_code == 201
    body = response.json()
    assert body["access_token"] == "signed-token"
    assert body["user"]["username"] == "user123"

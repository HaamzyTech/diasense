from app.core.config import Settings
from app.services.auth_service import AuthService, reset_auth_state


class DummyAuthUserRepo:
    def __init__(self) -> None:
        self.users: dict[str, dict] = {}

    def create_user(self, email: str, password_hash: str, role: str = "patient") -> dict:
        row = {
            "id": str(email),
            "email": email,
            "password_hash": password_hash,
            "role": role,
            "created_at": "2026-04-25T00:00:00Z",
        }
        self.users[email] = row
        return row

    def get_by_email(self, email: str) -> dict | None:
        return self.users.get(email)

    def update_password(self, email: str, password_hash: str) -> None:
        self.users[email]["password_hash"] = password_hash


def build_service() -> tuple[AuthService, DummyAuthUserRepo]:
    reset_auth_state("admin")
    repo = DummyAuthUserRepo()
    settings = Settings(
        BACKEND_ADMIN_USERNAME="admin",
        BACKEND_ADMIN_PASSWORD="admin",
        BACKEND_ADMIN_ROLE="admin",
        BACKEND_AUTH_SECRET_KEY="test-secret",
        BACKEND_AUTH_TOKEN_TTL_SECONDS=3600,
    )
    return AuthService(settings=settings, auth_user_repo=repo), repo


def test_auth_service_login_me_logout_flow() -> None:
    service, _repo = build_service()

    login_response = service.login("admin", "admin")
    assert login_response["token_type"] == "bearer"

    me_response = service.me(login_response["access_token"])
    assert me_response["user"]["username"] == "admin"

    reset_response = service.reset_password("admin", "new-password")
    assert reset_response["message"] == "Password updated successfully"

    logout_response = service.logout(login_response["access_token"])
    assert logout_response["message"] == "Logged out successfully"
    reset_auth_state("admin")


def test_signup_and_login_with_email_flow() -> None:
    service, _repo = build_service()

    signup_response = service.signup("user@example.com", "strongpass")
    assert signup_response["user"]["username"] == "user@example.com"
    assert signup_response["user"]["auth_source"] == "database"

    login_response = service.login("user@example.com", "strongpass")
    assert login_response["user"]["username"] == "user@example.com"

    me_response = service.me(login_response["access_token"])
    assert me_response["user"]["username"] == "user@example.com"

    reset_response = service.reset_password(
        current_password="strongpass",
        new_password="newstrongpass",
        token=login_response["access_token"],
    )
    assert reset_response["message"] == "Password updated successfully"

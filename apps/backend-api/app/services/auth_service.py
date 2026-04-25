from datetime import datetime, timezone
import re
from threading import Lock

from app.core.config import Settings
from app.core.exceptions import AuthenticationError, ConflictError, ValidationError
from app.core.security import create_signed_token, hash_password, verify_password, verify_signed_token
from app.core.time import to_iso8601, utc_now
from app.repositories.auth_user_repository import AuthUserRepository

_STATE_LOCK = Lock()
_CURRENT_ADMIN_PASSWORD: str | None = None
_REVOKED_TOKENS: set[str] = set()
EMAIL_PATTERN = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.IGNORECASE)


def reset_auth_state(password: str | None = None) -> None:
    global _CURRENT_ADMIN_PASSWORD
    with _STATE_LOCK:
        _CURRENT_ADMIN_PASSWORD = password
        _REVOKED_TOKENS.clear()


class AuthService:
    def __init__(self, settings: Settings, auth_user_repo: AuthUserRepository | None = None) -> None:
        self.settings = settings
        self.auth_user_repo = auth_user_repo
        global _CURRENT_ADMIN_PASSWORD
        with _STATE_LOCK:
            if _CURRENT_ADMIN_PASSWORD is None:
                _CURRENT_ADMIN_PASSWORD = settings.backend_admin_password

    def signup(self, email: str, password: str) -> dict:
        normalized_email = self._normalize_email(email)
        self._validate_password(password)
        repo = self._require_user_repo()
        existing_user = repo.get_by_email(normalized_email)
        if existing_user is not None:
            raise ConflictError(f"User with email {normalized_email} already exists")
        created_user = repo.create_user(
            email=normalized_email,
            password_hash=hash_password(password),
            role="patient",
        )
        return self._issue_token(
            subject=created_user["email"],
            role=created_user["role"],
            auth_source="database",
        )

    def login(self, username: str, password: str) -> dict:
        if username == self.settings.backend_admin_username:
            if password != self._admin_password:
                raise AuthenticationError("Invalid credentials")
            return self._issue_token(
                subject=self.settings.backend_admin_username,
                role=self.settings.backend_admin_role,
                auth_source="environment",
            )

        normalized_email = self._normalize_email(username)
        repo = self._require_user_repo()
        user = repo.get_by_email(normalized_email)
        if user is None or not verify_password(password, str(user["password_hash"])):
            raise AuthenticationError("Invalid credentials")
        return self._issue_token(
            subject=user["email"],
            role=user["role"],
            auth_source="database",
        )

    def logout(self, token: str) -> dict:
        self._validate_token(token)
        with _STATE_LOCK:
            _REVOKED_TOKENS.add(token)
        return {"message": "Logged out successfully"}

    def me(self, token: str) -> dict:
        claims = self._validate_token(token)
        auth_source = str(claims["auth_source"])
        username = str(claims["sub"])
        role = str(claims["role"])
        if auth_source == "database":
            user = self._require_user_repo().get_by_email(username)
            if user is None:
                raise AuthenticationError("Invalid access token")
            username = str(user["email"])
            role = str(user["role"])
        return {
            "user": self._user_payload(username=username, role=role, auth_source=auth_source),
            "session_expires_at": to_iso8601(datetime.fromtimestamp(int(claims["exp"]), tz=timezone.utc)),
        }

    def reset_password(self, current_password: str, new_password: str, token: str | None = None) -> dict:
        global _CURRENT_ADMIN_PASSWORD
        self._validate_password(new_password)
        if token is None:
            if current_password != self._admin_password:
                raise AuthenticationError("Current password is incorrect")
            with _STATE_LOCK:
                _CURRENT_ADMIN_PASSWORD = new_password
            return {"message": "Password updated successfully"}

        claims = self._validate_token(token)
        auth_source = str(claims["auth_source"])
        if auth_source == "environment":
            if current_password != self._admin_password:
                raise AuthenticationError("Current password is incorrect")
            with _STATE_LOCK:
                _CURRENT_ADMIN_PASSWORD = new_password
            return {"message": "Password updated successfully"}

        email = str(claims["sub"])
        repo = self._require_user_repo()
        user = repo.get_by_email(email)
        if user is None or not verify_password(current_password, str(user["password_hash"])):
            raise AuthenticationError("Current password is incorrect")
        repo.update_password(email=email, password_hash=hash_password(new_password))
        return {"message": "Password updated successfully"}

    @property
    def _admin_password(self) -> str:
        global _CURRENT_ADMIN_PASSWORD
        return _CURRENT_ADMIN_PASSWORD or self.settings.backend_admin_password

    def _validate_token(self, token: str) -> dict:
        with _STATE_LOCK:
            if token in _REVOKED_TOKENS:
                raise AuthenticationError("Access token has been revoked")
        claims = verify_signed_token(token, self.settings.backend_auth_secret_key)
        auth_source = str(claims.get("auth_source", ""))
        subject = str(claims.get("sub", ""))
        if auth_source == "environment":
            if subject != self.settings.backend_admin_username:
                raise AuthenticationError("Invalid access token")
            return claims
        if auth_source == "database":
            user = self._require_user_repo().get_by_email(subject)
            if user is None:
                raise AuthenticationError("Invalid access token")
            return claims
        raise AuthenticationError("Invalid access token")

    def _user_payload(self, username: str, role: str, auth_source: str) -> dict:
        return {
            "username": username,
            "role": role,
            "auth_source": auth_source,
        }

    def _issue_token(self, subject: str, role: str, auth_source: str) -> dict:
        expires_at = utc_now().timestamp() + self.settings.backend_auth_token_ttl_seconds
        token = create_signed_token(
            {
                "sub": subject,
                "role": role,
                "auth_source": auth_source,
                "exp": int(expires_at),
            },
            self.settings.backend_auth_secret_key,
        )
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": self.settings.backend_auth_token_ttl_seconds,
            "user": self._user_payload(username=subject, role=role, auth_source=auth_source),
        }

    def _normalize_email(self, email: str) -> str:
        normalized_email = email.strip().lower()
        if not normalized_email or EMAIL_PATTERN.fullmatch(normalized_email) is None:
            raise ValidationError("A valid email address is required")
        return normalized_email

    def _require_user_repo(self) -> AuthUserRepository:
        if self.auth_user_repo is None:
            raise ValidationError("Auth user repository is not configured")
        return self.auth_user_repo

    def _validate_password(self, password: str) -> None:
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long")

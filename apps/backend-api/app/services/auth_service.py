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
USERNAME_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{1,48}[a-z0-9])?$")
VALID_ROLES = {"patient", "clinician", "admin"}


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

    def signup(self, username: str | None, email: str | None, password: str) -> dict:
        normalized_username = self._normalize_username(username) if username else None
        normalized_email = self._normalize_email(email) if email else None

        if normalized_username is None and normalized_email is None:
            raise ValidationError("Provide a username or email address to create an account")

        self._validate_password(password)
        repo = self._require_user_repo()
        resolved_username = normalized_username or self._generate_username_from_email(normalized_email, repo)

        existing_username = repo.get_by_username(resolved_username)
        if existing_username is not None:
            raise ConflictError(f"User with username {resolved_username} already exists")

        if normalized_email is not None:
            existing_email = repo.get_by_email(normalized_email)
            if existing_email is not None:
                raise ConflictError(f"User with email {normalized_email} already exists")

        created_user = repo.create_user(
            username=resolved_username,
            email=normalized_email,
            password_hash=hash_password(password),
            role="patient",
        )
        return self._issue_token(
            subject=created_user["username"],
            role=created_user["role"],
            auth_source="database",
            email=created_user.get("email"),
        )

    def login(self, username: str, password: str) -> dict:
        normalized_identifier = username.strip()
        if normalized_identifier == self.settings.backend_admin_username:
            if password != self._admin_password:
                raise AuthenticationError("Invalid credentials")
            return self._issue_token(
                subject=self.settings.backend_admin_username,
                role=self.settings.backend_admin_role,
                auth_source="environment",
                email=None,
            )

        repo = self._require_user_repo()
        if "@" in normalized_identifier:
            normalized_email = self._normalize_email(normalized_identifier)
            user = repo.get_by_email(normalized_email)
        else:
            normalized_username = self._normalize_username(normalized_identifier)
            user = repo.get_by_username(normalized_username)
        if user is None or not verify_password(password, str(user["password_hash"])):
            raise AuthenticationError("Invalid credentials")
        return self._issue_token(
            subject=user["username"],
            role=user["role"],
            auth_source="database",
            email=user.get("email"),
        )

    def logout(self, token: str) -> dict:
        self._validate_token(token)
        with _STATE_LOCK:
            _REVOKED_TOKENS.add(token)
        return {"message": "Logged out successfully"}

    def me(self, token: str) -> dict:
        claims = self._validate_token(token)
        user = self._resolve_user_from_claims(claims)
        return {
            "user": user,
            "session_expires_at": to_iso8601(datetime.fromtimestamp(int(claims["exp"]), tz=timezone.utc)),
        }

    def authenticate(self, token: str) -> dict:
        claims = self._validate_token(token)
        return self._resolve_user_from_claims(claims)

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

        username = str(claims["sub"])
        repo = self._require_user_repo()
        user = repo.get_by_username(username)
        if user is None or not verify_password(current_password, str(user["password_hash"])):
            raise AuthenticationError("Current password is incorrect")
        repo.update_password(user_id=user["id"], password_hash=hash_password(new_password))
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
            user = self._require_user_repo().get_by_username(subject)
            if user is None:
                raise AuthenticationError("Invalid access token")
            return claims
        raise AuthenticationError("Invalid access token")

    def _resolve_user_from_claims(self, claims: dict) -> dict:
        auth_source = str(claims["auth_source"])
        username = str(claims["sub"])
        role = str(claims["role"])
        email = None
        if auth_source == "database":
            user = self._require_user_repo().get_by_username(username)
            if user is None:
                raise AuthenticationError("Invalid access token")
            username = str(user["username"])
            email = str(user["email"]) if user.get("email") else None
            role = str(user["role"])
        return self._user_payload(username=username, email=email, role=role, auth_source=auth_source)

    def _user_payload(self, username: str, email: str | None, role: str, auth_source: str) -> dict:
        return {
            "username": username,
            "email": email,
            "role": role,
            "auth_source": auth_source,
        }

    def _issue_token(self, subject: str, role: str, auth_source: str, email: str | None) -> dict:
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
            "user": self._user_payload(username=subject, email=email, role=role, auth_source=auth_source),
        }

    def _normalize_email(self, email: str) -> str:
        normalized_email = email.strip().lower()
        if not normalized_email or EMAIL_PATTERN.fullmatch(normalized_email) is None:
            raise ValidationError("A valid email address is required")
        return normalized_email

    def _normalize_username(self, username: str) -> str:
        normalized_username = username.strip().lower()
        if not normalized_username or USERNAME_PATTERN.fullmatch(normalized_username) is None:
            raise ValidationError(
                "Use 3-50 lowercase letters, numbers, dots, hyphens, or underscores for the username"
            )
        return normalized_username

    def _generate_username_from_email(self, email: str | None, repo: AuthUserRepository) -> str:
        if email is None:
            raise ValidationError("A username or email address is required")

        local_part = email.split("@", maxsplit=1)[0].strip().lower()
        collapsed = re.sub(r"[^a-z0-9._-]+", "-", local_part).strip("._-") or "user"
        candidate = collapsed if USERNAME_PATTERN.fullmatch(collapsed) else f"user-{collapsed[:20]}".strip("-")
        candidate = candidate[:50].rstrip("._-") or "user"

        if len(candidate) < 3:
            candidate = f"user-{candidate}".strip("-")

        unique_candidate = candidate
        suffix = 2
        while repo.get_by_username(unique_candidate) is not None:
            suffix_token = f"-{suffix}"
            unique_candidate = f"{candidate[: 50 - len(suffix_token)]}{suffix_token}"
            suffix += 1
        return unique_candidate

    def _require_user_repo(self) -> AuthUserRepository:
        if self.auth_user_repo is None:
            raise ValidationError("Auth user repository is not configured")
        return self.auth_user_repo

    def _validate_password(self, password: str) -> None:
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long")

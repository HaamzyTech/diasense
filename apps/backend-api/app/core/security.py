import base64
import hashlib
import hmac
import json
import secrets
from typing import Any

from app.core.exceptions import AuthenticationError
from app.core.time import utc_now


def _encode_segment(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).decode("utf-8").rstrip("=")


def _decode_segment(payload: str) -> bytes:
    padding = "=" * (-len(payload) % 4)
    return base64.urlsafe_b64decode(f"{payload}{padding}".encode("utf-8"))


def create_signed_token(claims: dict[str, Any], secret_key: str) -> str:
    body = json.dumps(claims, separators=(",", ":"), sort_keys=True).encode("utf-8")
    signature = hmac.new(secret_key.encode("utf-8"), body, hashlib.sha256).digest()
    return f"{_encode_segment(body)}.{_encode_segment(signature)}"


def verify_signed_token(token: str, secret_key: str) -> dict[str, Any]:
    try:
        payload_segment, signature_segment = token.split(".", maxsplit=1)
    except ValueError as exc:
        raise AuthenticationError("Invalid access token") from exc

    payload = _decode_segment(payload_segment)
    expected_signature = hmac.new(secret_key.encode("utf-8"), payload, hashlib.sha256).digest()
    actual_signature = _decode_segment(signature_segment)
    if not hmac.compare_digest(expected_signature, actual_signature):
        raise AuthenticationError("Invalid access token")

    claims = json.loads(payload.decode("utf-8"))
    expires_at = claims.get("exp")
    if not isinstance(expires_at, int) or expires_at <= int(utc_now().timestamp()):
        raise AuthenticationError("Access token has expired")
    return claims


def hash_password(password: str, iterations: int = 390000) -> str:
    salt = secrets.token_hex(16)
    derived_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
    return f"pbkdf2_sha256${iterations}${salt}${derived_key.hex()}"


def verify_password(password: str, encoded_password: str) -> bool:
    try:
        algorithm, iteration_text, salt, digest = encoded_password.split("$", maxsplit=3)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        int(iteration_text),
    )
    return hmac.compare_digest(derived_key.hex(), digest)

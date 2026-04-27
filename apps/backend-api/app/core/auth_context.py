from dataclasses import dataclass


@dataclass(frozen=True)
class CurrentUser:
    username: str
    email: str | None
    role: str
    auth_source: str
    access_token: str

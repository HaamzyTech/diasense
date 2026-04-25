from app.schemas.base import APIModel


class AuthUser(APIModel):
    username: str
    role: str
    auth_source: str


class LoginRequest(APIModel):
    username: str
    password: str


class SignupRequest(APIModel):
    email: str
    password: str


class LoginResponse(APIModel):
    access_token: str
    token_type: str
    expires_in: int
    user: AuthUser


class SignupResponse(LoginResponse):
    pass


class LogoutRequest(APIModel):
    access_token: str | None = None


class LogoutResponse(APIModel):
    message: str


class MeRequest(APIModel):
    access_token: str | None = None


class MeResponse(APIModel):
    user: AuthUser
    session_expires_at: str


class ResetPasswordRequest(APIModel):
    current_password: str
    new_password: str
    access_token: str | None = None


class ResetPasswordResponse(APIModel):
    message: str

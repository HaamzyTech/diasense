from fastapi import APIRouter, Request, status

from app.api.deps import db_session_scope, get_auth_service
from app.core.exceptions import AuthenticationError
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    LogoutResponse,
    MeRequest,
    MeResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    SignupRequest,
    SignupResponse,
)
from app.services.auth_service import AuthService

router = APIRouter()


def _resolve_access_token(request: Request, body_token: str | None) -> str:
    authorization = request.headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        return authorization.split(" ", maxsplit=1)[1].strip()
    if body_token:
        return body_token
    raise AuthenticationError("Access token is required")


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest) -> SignupResponse:
    with db_session_scope() as db:
        service: AuthService = get_auth_service(db)
        result = service.signup(payload.email, payload.password)
        return SignupResponse(**result)


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest) -> LoginResponse:
    with db_session_scope() as db:
        service: AuthService = get_auth_service(db)
        result = service.login(payload.username, payload.password)
        return LoginResponse(**result)


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: Request,
    payload: LogoutRequest | None = None,
) -> LogoutResponse:
    with db_session_scope() as db:
        service: AuthService = get_auth_service(db)
        token = _resolve_access_token(request, payload.access_token if payload else None)
        result = service.logout(token)
        return LogoutResponse(**result)


@router.post("/me", response_model=MeResponse)
async def me(
    request: Request,
    payload: MeRequest | None = None,
) -> MeResponse:
    with db_session_scope() as db:
        service: AuthService = get_auth_service(db)
        token = _resolve_access_token(request, payload.access_token if payload else None)
        result = service.me(token)
        return MeResponse(**result)


@router.post("/reset-password", response_model=ResetPasswordResponse, status_code=status.HTTP_200_OK)
async def reset_password(request: Request, payload: ResetPasswordRequest) -> ResetPasswordResponse:
    with db_session_scope() as db:
        service: AuthService = get_auth_service(db)
        token = None
        if payload.access_token is not None or request.headers.get("authorization"):
            token = _resolve_access_token(request, payload.access_token)
        result = service.reset_password(payload.current_password, payload.new_password, token=token)
        return ResetPasswordResponse(**result)

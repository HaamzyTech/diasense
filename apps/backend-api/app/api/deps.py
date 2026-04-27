from contextlib import contextmanager
from typing import Iterable

from fastapi import Request
from sqlalchemy.orm import Session

from app.clients.model_server import ModelServerClient
from app.core.config import Settings, get_settings
from app.core.auth_context import CurrentUser
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.db.session import SessionLocal, get_db
from app.repositories.auth_user_repository import AuthUserRepository
from app.repositories.drift_repository import DriftRepository
from app.repositories.feedback_repository import FeedbackRepository
from app.repositories.model_version_repository import ModelVersionRepository
from app.repositories.pipeline_repository import PipelineRepository
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.system_event_repository import SystemEventRepository
from app.services.auth_service import AuthService
from app.services.drift_service import DriftService
from app.services.feedback_service import FeedbackService
from app.services.health_service import HealthService
from app.services.model_registry_service import ModelRegistryService
from app.services.ops_service import OpsService
from app.services.pipeline_service import PipelineService
from app.services.prediction_service import PredictionService
from app.services.user_service import UserService


def resolve_access_token(request: Request, body_token: str | None = None) -> str:
    authorization = request.headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        return authorization.split(" ", maxsplit=1)[1].strip()
    if body_token:
        return body_token
    raise AuthenticationError("Access token is required")


def require_current_user(db: Session, request: Request, body_token: str | None = None) -> CurrentUser:
    service = get_auth_service(db)
    token = resolve_access_token(request, body_token)
    user = service.authenticate(token)
    return CurrentUser(
        username=str(user["username"]),
        email=str(user["email"]) if user.get("email") else None,
        role=str(user["role"]),
        auth_source=str(user["auth_source"]),
        access_token=token,
    )


def require_roles(user: CurrentUser, allowed_roles: Iterable[str]) -> None:
    if user.role not in set(allowed_roles):
        raise AuthorizationError()


def get_app_settings() -> Settings:
    return get_settings()


@contextmanager
def db_session_scope():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_prediction_service(db: Session) -> PredictionService:
    return PredictionService(
        prediction_repo=PredictionRepository(db),
        model_repo=ModelVersionRepository(db),
        model_server_client=ModelServerClient(),
        system_event_repo=SystemEventRepository(db),
        auth_user_repo=AuthUserRepository(db),
    )


def get_model_registry_service(db: Session) -> ModelRegistryService:
    return ModelRegistryService(model_repo=ModelVersionRepository(db))


def get_drift_service(db: Session) -> DriftService:
    return DriftService(drift_repo=DriftRepository(db))


def get_pipeline_service(db: Session) -> PipelineService:
    return PipelineService(pipeline_repo=PipelineRepository(db))


def get_feedback_service(db: Session) -> FeedbackService:
    return FeedbackService(
        feedback_repo=FeedbackRepository(db),
        prediction_repo=PredictionRepository(db),
    )


def get_health_service(db: Session) -> HealthService:
    return HealthService(settings=get_settings(), db=db)


def get_auth_service(db: Session) -> AuthService:
    return AuthService(settings=get_settings(), auth_user_repo=AuthUserRepository(db))


def get_user_service(db: Session) -> UserService:
    auth_user_repo = AuthUserRepository(db)
    return UserService(
        auth_user_repo=auth_user_repo,
        auth_service=AuthService(settings=get_settings(), auth_user_repo=auth_user_repo),
    )


def get_ops_service(db: Session) -> OpsService:
    return OpsService(
        settings=get_settings(),
        health_service=get_health_service(db),
        model_registry_service=get_model_registry_service(db),
        pipeline_service=get_pipeline_service(db),
        drift_service=get_drift_service(db),
    )

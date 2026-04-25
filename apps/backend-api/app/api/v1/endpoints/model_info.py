from fastapi import APIRouter

from app.api.deps import db_session_scope, get_model_registry_service
from app.core.time import to_iso8601
from app.schemas.model_info import ModelInfoResponse
from app.services.model_registry_service import ModelRegistryService

router = APIRouter(prefix="/model")


@router.get("/info", response_model=ModelInfoResponse)
async def get_model_info() -> ModelInfoResponse:
    with db_session_scope() as db:
        service: ModelRegistryService = get_model_registry_service(db)
        model = service.get_active_model()
        return ModelInfoResponse(
            model_name=model["model_name"],
            model_version=model["model_version"],
            algorithm=model["algorithm"],
            stage=model["stage"],
            mlflow_run_id=model["mlflow_run_id"],
            mlflow_model_uri=model["mlflow_model_uri"],
            metrics=model["metrics"] or {},
            params=model["params"] or {},
            created_at=to_iso8601(model.get("created_at")),
        )

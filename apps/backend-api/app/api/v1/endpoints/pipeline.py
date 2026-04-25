from fastapi import APIRouter, Query

from app.api.deps import db_session_scope, get_pipeline_service
from app.schemas.pipeline import PipelineRunsResponse
from app.services.pipeline_service import PipelineService

router = APIRouter(prefix="/pipeline")


@router.get("/runs", response_model=PipelineRunsResponse)
async def list_pipeline_runs(
    limit: int = Query(default=20, ge=1, le=100),
) -> PipelineRunsResponse:
    with db_session_scope() as db:
        service: PipelineService = get_pipeline_service(db)
        return PipelineRunsResponse(**service.list_runs(limit=limit))

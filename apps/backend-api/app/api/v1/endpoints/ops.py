from fastapi import APIRouter

from app.api.deps import db_session_scope, get_ops_service
from app.schemas.ops import OpsSummaryResponse
from app.services.ops_service import OpsService

router = APIRouter(prefix="/ops")


@router.get("/summary", response_model=OpsSummaryResponse)
async def get_ops_summary() -> OpsSummaryResponse:
    with db_session_scope() as db:
        service: OpsService = get_ops_service(db)
        return OpsSummaryResponse(**service.summary())

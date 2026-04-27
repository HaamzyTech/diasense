from fastapi import APIRouter, Request

from app.api.deps import db_session_scope, get_ops_service, require_current_user, require_roles
from app.schemas.ops import OpsSummaryResponse
from app.services.ops_service import OpsService

router = APIRouter(prefix="/ops")


@router.get("/summary", response_model=OpsSummaryResponse)
async def get_ops_summary(request: Request) -> OpsSummaryResponse:
    with db_session_scope() as db:
        current_user = require_current_user(db, request)
        require_roles(current_user, {"admin"})
        service: OpsService = get_ops_service(db)
        return OpsSummaryResponse(**service.summary())

from uuid import UUID

from fastapi import APIRouter, Query, Request

from app.api.deps import db_session_scope, get_user_service, require_current_user
from app.schemas.users import DeleteUserResponse, UpdateUserRoleRequest, UserListResponse, UserSummary
from app.services.user_service import UserService

router = APIRouter(prefix="/users")


@router.get("", response_model=UserListResponse)
async def list_users(
    request: Request,
    limit: int = Query(default=200, ge=1, le=500),
) -> UserListResponse:
    with db_session_scope() as db:
        current_user = require_current_user(db, request)
        service: UserService = get_user_service(db)
        return UserListResponse(**service.list_users(current_user=current_user, limit=limit))


@router.patch("/{user_id}/role", response_model=UserSummary)
async def update_user_role(
    request: Request,
    user_id: UUID,
    payload: UpdateUserRoleRequest,
) -> UserSummary:
    with db_session_scope() as db:
        current_user = require_current_user(db, request)
        service: UserService = get_user_service(db)
        return UserSummary(**service.update_user_role(current_user=current_user, user_id=user_id, role=payload.role))


@router.delete("/{user_id}", response_model=DeleteUserResponse)
async def delete_user(
    request: Request,
    user_id: UUID,
) -> DeleteUserResponse:
    with db_session_scope() as db:
        current_user = require_current_user(db, request)
        service: UserService = get_user_service(db)
        return DeleteUserResponse(**service.delete_user(current_user=current_user, user_id=user_id))

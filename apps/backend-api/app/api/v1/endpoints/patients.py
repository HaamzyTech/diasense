from uuid import UUID

from fastapi import APIRouter, Query, Request, status

from app.api.deps import db_session_scope, get_user_service, require_current_user
from app.schemas.users import (
    CreatePatientRequest,
    CreatePatientResponse,
    DeletePatientResponse,
    PatientListResponse,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/patients")


@router.post("", response_model=CreatePatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    request: Request,
    payload: CreatePatientRequest,
) -> CreatePatientResponse:
    with db_session_scope() as db:
        current_user = require_current_user(db, request)
        service: UserService = get_user_service(db)
        return CreatePatientResponse(
            **service.create_patient(
                current_user=current_user,
                username=payload.username,
                email=payload.email,
                password=payload.password,
            )
        )


@router.get("", response_model=PatientListResponse)
async def list_patients(
    request: Request,
    limit: int = Query(default=200, ge=1, le=500),
) -> PatientListResponse:
    with db_session_scope() as db:
        current_user = require_current_user(db, request)
        service: UserService = get_user_service(db)
        return PatientListResponse(**service.list_patients(current_user=current_user, limit=limit))


@router.delete("/{patient_id}", response_model=DeletePatientResponse)
async def delete_patient(
    request: Request,
    patient_id: UUID,
) -> DeletePatientResponse:
    with db_session_scope() as db:
        current_user = require_current_user(db, request)
        service: UserService = get_user_service(db)
        return DeletePatientResponse(
            **service.delete_patient(current_user=current_user, user_id=patient_id)
        )

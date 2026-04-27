from typing import Literal
from uuid import UUID

from pydantic import Field

from app.schemas.base import APIModel


RoleValue = Literal["patient", "clinician", "admin"]


class UserSummary(APIModel):
    id: UUID
    username: str
    email: str | None = None
    role: RoleValue
    created_at: str


class UserListResponse(APIModel):
    items: list[UserSummary]
    count: int


class UpdateUserRoleRequest(APIModel):
    role: RoleValue


class DeleteUserResponse(APIModel):
    message: str
    user: UserSummary


class CreatePatientRequest(APIModel):
    username: str | None = None
    email: str | None = None
    password: str


class CreatePatientResponse(APIModel):
    message: str
    patient: UserSummary


class DeletePatientResponse(APIModel):
    message: str
    patient: UserSummary


class PatientSummary(APIModel):
    id: UUID
    username: str
    email: str | None = None
    role: RoleValue
    created_at: str
    assessment_count: int = Field(default=0, ge=0)
    last_assessed_at: str | None = None
    latest_risk_band: str | None = None
    latest_risk_probability: float | None = None


class PatientListResponse(APIModel):
    items: list[PatientSummary]
    count: int

from uuid import UUID

from pydantic import Field

from app.schemas.base import APIModel


class PredictRequest(APIModel):
    patient_email: str | None = None
    pregnancies: int = Field(ge=0, le=30)
    glucose: float = Field(ge=0, le=300)
    blood_pressure: float = Field(ge=0, le=200)
    skin_thickness: float = Field(ge=0, le=100)
    insulin: float = Field(ge=0, le=1000)
    bmi: float = Field(ge=0, le=100)
    diabetes_pedigree_function: float = Field(ge=0, le=10)
    age: int = Field(ge=1, le=120)


class TopFactor(APIModel):
    feature: str
    importance: float


class PredictResponse(APIModel):
    request_id: UUID
    model_version_id: UUID
    submitted_by: str
    patient_email: str
    predicted_label: bool
    risk_probability: float
    risk_band: str
    interpretation: str
    top_factors: list[TopFactor]
    latency_ms: int
    created_at: str


class PredictionRequestRecord(APIModel):
    id: UUID
    session_id: UUID
    submitted_by: str
    patient_email: str
    actor_role: str
    pregnancies: int
    glucose: float
    blood_pressure: float
    skin_thickness: float
    insulin: float
    bmi: float
    diabetes_pedigree_function: float
    age: int
    source: str
    created_at: str | None = None


class PredictionResultRecord(APIModel):
    id: UUID | None = None
    model_version_id: UUID | None = None
    predicted_label: bool | None = None
    risk_probability: float | None = None
    risk_band: str | None = None
    interpretation: str | None = None
    top_factors: list[TopFactor] = Field(default_factory=list)
    latency_ms: int | None = None
    created_at: str | None = None


class PredictionDetailResponse(APIModel):
    request: PredictionRequestRecord
    result: PredictionResultRecord | None = None


class PredictionListItem(APIModel):
    request_id: UUID
    submitted_by: str
    patient_email: str
    actor_role: str
    risk_probability: float
    risk_band: str
    predicted_label: bool
    interpretation: str
    created_at: str | None = None


class PredictionListResponse(APIModel):
    items: list[PredictionListItem]
    count: int


class DeletePredictionResponse(APIModel):
    message: str
    request_id: UUID
    patient_email: str
    submitted_by: str
    actor_role: str
    deleted_at: str


class MyPredictionsRequest(APIModel):
    limit: int = Field(default=20, ge=1, le=100)

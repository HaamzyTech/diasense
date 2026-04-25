from app.schemas.base import APIModel


class DriftFeature(APIModel):
    feature_name: str
    baseline_mean: float
    current_mean: float
    baseline_variance: float
    current_variance: float
    psi: float | None = None
    ks_stat: float | None = None
    status: str


class DriftResponse(APIModel):
    report_date: str
    overall_status: str
    features: list[DriftFeature]

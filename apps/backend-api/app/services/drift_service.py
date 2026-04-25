from app.repositories.drift_repository import DriftRepository


class DriftService:
    def __init__(self, drift_repo: DriftRepository) -> None:
        self.drift_repo = drift_repo

    def latest(self) -> dict:
        report_date, features = self.drift_repo.latest()
        if not report_date:
            return {"report_date": "", "overall_status": "unknown", "features": []}
        overall = "stable" if all(item.get("status") == "stable" for item in features) else "attention"
        return {"report_date": report_date, "overall_status": overall, "features": features}

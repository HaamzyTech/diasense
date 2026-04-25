from sqlalchemy import text
from sqlalchemy.orm import Session


class DriftRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def latest(self) -> tuple[str | None, list[dict]]:
        date_stmt = text("SELECT MAX(report_date) AS report_date FROM drift_reports")
        row = self.db.execute(date_stmt).mappings().first()
        if not row or row["report_date"] is None:
            return None, []

        report_date = str(row["report_date"])
        item_stmt = text(
            """
            SELECT feature_name, baseline_mean, current_mean, baseline_variance, current_variance, psi, ks_stat, status
            FROM drift_reports
            WHERE report_date = :report_date
            ORDER BY feature_name ASC
            """
        )
        items = self.db.execute(item_stmt, {"report_date": report_date}).mappings().all()
        return report_date, [dict(item) for item in items]

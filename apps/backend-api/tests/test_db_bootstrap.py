from app.db.bootstrap import BASE_REVISION, HEAD_REVISION, _infer_existing_revision


class FakeInspector:
    def __init__(self, columns_by_table: dict[str, list[str]]) -> None:
        self.columns_by_table = columns_by_table

    def get_columns(self, table_name: str) -> list[dict[str, str]]:
        return [{"name": column_name} for column_name in self.columns_by_table[table_name]]


def test_infer_existing_revision_for_first_boot_init_schema() -> None:
    inspector = FakeInspector(
        {
            "model_versions": ["id"],
            "prediction_requests": [
                "id",
                "session_id",
                "actor_role",
                "pregnancies",
                "glucose",
                "blood_pressure",
                "skin_thickness",
                "insulin",
                "bmi",
                "diabetes_pedigree_function",
                "age",
                "source",
                "created_at",
            ],
            "prediction_results": ["id"],
            "feedback_labels": ["id"],
            "drift_reports": ["id"],
            "pipeline_runs": ["id"],
            "system_events": ["id"],
        }
    )

    inferred_revision = _infer_existing_revision(inspector, set(inspector.columns_by_table))

    assert inferred_revision == BASE_REVISION


def test_infer_existing_revision_for_latest_auth_schema() -> None:
    inspector = FakeInspector(
        {
            "auth_users": ["id", "username", "email", "password_hash", "role", "created_at"],
            "prediction_requests": [
                "id",
                "session_id",
                "submitted_by",
                "patient_email",
                "actor_role",
            ],
        }
    )

    inferred_revision = _infer_existing_revision(inspector, set(inspector.columns_by_table))

    assert inferred_revision == HEAD_REVISION

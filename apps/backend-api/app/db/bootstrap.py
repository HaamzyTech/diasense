from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from app.core.config import get_settings

HEAD_REVISION = "0004_auth_usernames"
BASE_REVISION = "0001_initial_schema"
MANAGED_TABLES = {
    "auth_users",
    "model_versions",
    "prediction_requests",
    "prediction_results",
    "feedback_labels",
    "drift_reports",
    "pipeline_runs",
    "system_events",
}
BASE_SCHEMA_TABLES = MANAGED_TABLES - {"auth_users"}


def _get_column_names(inspector, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}


def _has_alembic_revision_table(existing_tables: set[str]) -> bool:
    return "alembic_version" in existing_tables


def _get_stored_revision(engine) -> str | None:
    with engine.begin() as connection:
        row = connection.execute(
            text("SELECT version_num FROM alembic_version LIMIT 1")
        ).first()
    return str(row[0]) if row else None


def _infer_existing_revision(inspector, existing_tables: set[str]) -> str | None:
    if "auth_users" not in existing_tables:
        if BASE_SCHEMA_TABLES.issubset(existing_tables):
            return BASE_REVISION
        return None

    auth_user_columns = _get_column_names(inspector, "auth_users")
    prediction_request_columns = _get_column_names(inspector, "prediction_requests")

    if "username" in auth_user_columns:
        return "0004_auth_usernames"

    if {
        "submitted_by",
        "patient_email",
    }.issubset(prediction_request_columns):
        return "0003_prediction_ownership"

    return "0002_auth_users"


def _set_alembic_revision(engine, revision: str) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS alembic_version (
                    version_num VARCHAR(32) NOT NULL PRIMARY KEY
                )
                """
            )
        )
        connection.execute(text("DELETE FROM alembic_version"))
        connection.execute(
            text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
            {"revision": revision},
        )


def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.sqlalchemy_database_uri, pool_pre_ping=True)
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", settings.sqlalchemy_database_uri)

    if existing_tables & MANAGED_TABLES:
        inferred_revision = _infer_existing_revision(inspector, existing_tables)
        if inferred_revision is None:
            command.upgrade(config, "head")
            return

        if _has_alembic_revision_table(existing_tables):
            stored_revision = _get_stored_revision(engine)
            if stored_revision != inferred_revision:
                _set_alembic_revision(engine, inferred_revision)
            command.upgrade(config, "head")
            return

        _set_alembic_revision(engine, inferred_revision)
        if inferred_revision != HEAD_REVISION:
            command.upgrade(config, "head")
        return

    command.upgrade(config, "head")


if __name__ == "__main__":
    main()

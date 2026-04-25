from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from app.core.config import get_settings

HEAD_REVISION = "0002_auth_users"
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

    if MANAGED_TABLES.issubset(existing_tables):
        _set_alembic_revision(engine, HEAD_REVISION)
        return

    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", settings.sqlalchemy_database_uri)
    command.upgrade(config, "head")


if __name__ == "__main__":
    main()

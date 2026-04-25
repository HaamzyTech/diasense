from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="backend-api")
    app_version: str = Field(default="0.1.0")
    app_env: str = Field(default="development")

    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    postgres_host: str = Field(default="postgres")
    postgres_port: int = Field(default=5432)
    postgres_db: str = Field(default="diasense")
    postgres_user: str = Field(default="diasense")
    postgres_password: str = Field(default="diasense")

    model_server_url: str = Field(default="http://model-server:5001")
    mlflow_tracking_uri: str = Field(default="http://mlflow-tracking:5000")
    request_timeout_seconds: float = Field(default=10.0)

    backend_admin_username: str = Field(default="admin")
    backend_admin_password: str = Field(default="admin")
    backend_admin_role: str = Field(default="admin")
    backend_auth_secret_key: str = Field(default="diasense-dev-secret")
    backend_auth_token_ttl_seconds: int = Field(default=43200)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
        extra="ignore",
    )

    @property
    def sqlalchemy_database_uri(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

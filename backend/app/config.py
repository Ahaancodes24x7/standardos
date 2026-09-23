"""Runtime configuration from environment variables (and an optional .env file)."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    # Postgres connection string, e.g. postgresql://user:pass@localhost:5432/standardos
    database_url: Optional[str] = None
    # Max connections per server instance (keep small on serverless).
    database_pool_max: int = 5
    # Optional direct connection for migrations; falls back to DATABASE_URL.
    db_migration_url: Optional[str] = None

    # 32+ random characters used to sign the session cookie.
    session_secret: Optional[str] = None
    session_cookie_name: str = "standardos_session"
    session_max_age_seconds: int = 60 * 60 * 24 * 30
    # Set true when the API is served over HTTPS.
    session_cookie_secure: bool = False

    # Bearer secret(s) for GET /api/cron/analysis-sweeper.
    cron_secret: Optional[str] = None
    cron_secret_previous: Optional[str] = None

    # Comma-separated origins allowed to call the API with credentials.
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000"

    # "on" enables LLM copy-editing of repair wording (read by standardos_aiml).
    standardos_llm_repair: str = "off"

    # Maximum pasted-text length for an analysis.
    max_text_chars: int = 100_000

    @field_validator("database_url", "db_migration_url")
    @classmethod
    def _sqlalchemy_url(cls, value: Optional[str]) -> Optional[str]:
        """Accept postgres:// and postgresql:// URLs; SQLAlchemy needs the psycopg driver name."""
        if not value:
            return value
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value[len(prefix) :]
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

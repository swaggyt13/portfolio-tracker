"""Centralized settings loaded from environment variables."""
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # IBKR
    ibkr_host: str = Field(default="127.0.0.1", alias="IBKR_HOST")
    ibkr_port: int = Field(default=7497, alias="IBKR_PORT")
    ibkr_client_id: int = Field(default=11, alias="IBKR_CLIENT_ID")
    ibkr_timeout: int = Field(default=15, alias="IBKR_TIMEOUT")
    ibkr_readonly: bool = Field(default=True, alias="IBKR_READONLY")

    # Database
    database_url: str = Field(
        default="postgresql+psycopg2://postgres:postgres@localhost:5432/portfolio",
        alias="DATABASE_URL",
    )

    # Scheduler
    sync_interval_minutes: int = Field(default=15, alias="SYNC_INTERVAL_MINUTES")
    sync_on_startup: bool = Field(default=True, alias="SYNC_ON_STARTUP")

    # CORS
    cors_origins_raw: str = Field(
        default="http://localhost:5173", alias="CORS_ORIGINS"
    )

    # Notifications
    notify_drop_threshold_pct: float = Field(default=-10.0, alias="NOTIFY_DROP_THRESHOLD_PCT")

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

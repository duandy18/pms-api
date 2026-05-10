# app/settings.py
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PmsApiSettings(BaseSettings):
    """
    PMS API settings.

    Database rule:
    - PMS API reads PMS_DATABASE_URL only.
    - Do not fallback to WMS_DATABASE_URL.
    - Database is optional at import time so contract-only tests can run without DB.
    """

    env: str = Field(default="dev")
    database_url: str | None = Field(default=None)
    sql_echo: bool = Field(default=False)

    model_config = SettingsConfigDict(
        env_prefix="PMS_",
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> PmsApiSettings:
    return PmsApiSettings()

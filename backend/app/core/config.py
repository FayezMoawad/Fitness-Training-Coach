"""Application configuration, loaded from environment variables.

Never hardcode secrets here — all values are sourced from the environment
(see `.env.example` for the full list of expected variables). Values are
optional at this scaffolding stage so the app can boot without a full
environment configured; later steps (DB, auth) will depend on them being set.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str | None = None
    jwt_secret: str | None = None
    jwt_expire_minutes: int = 30


settings = Settings()

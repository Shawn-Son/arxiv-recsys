from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ASTER_",
        extra="ignore",
    )

    environment: str = "development"
    log_level: str = "INFO"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    request_timeout_seconds: float = 15.0
    fixture_repository: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()

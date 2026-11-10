"""Load and validate application settings from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application configuration shared across runtime components."""

    app_name: str = "My Fitness Coach API"
    app_env: Literal["development", "test", "production"] = "development"
    debug: bool = False
    database_url: str = "postgresql+asyncpg://localhost/fitness"
    log_level: str = "INFO"
    auth_secret_key: str = "development-only-change-this-secret-key"
    access_token_expire_minutes: int = 30

    @model_validator(mode="after")
    def validate_auth_settings(self) -> "Settings":
        """Reject unsafe production signing keys and invalid token lifetimes."""
        if self.access_token_expire_minutes < 1:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be positive")
        if self.app_env == "production" and (
            len(self.auth_secret_key) < 32
            or self.auth_secret_key == "development-only-change-this-secret-key"
        ):
            raise ValueError("AUTH_SECRET_KEY must be a unique secret of at least 32 characters")
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return one validated settings object for the current process."""
    return Settings()

import secrets
from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: Literal["development", "test", "production"] = "development"
    debug: bool = False
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/portfolio"
    frontend_url: str = "http://localhost:5173"
    site_url: str = "http://localhost:5173"
    public_site_url: str | None = None
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(48))
    access_token_expire_minutes: int = Field(default=15, ge=1, le=60)
    refresh_token_expire_days: int = Field(default=30, ge=1, le=90)
    telegram_bot_token: str = ""
    telegram_channel_id: str = ""
    telegram_channel_url: str = ""
    upload_dir: Path = Path("uploads")
    max_image_upload_mb: int = Field(default=10, ge=1, le=25)

    @model_validator(mode="after")
    def validate_settings(self):
        if self.public_site_url:
            self.site_url = self.public_site_url.rstrip("/")
        for value in [self.frontend_url, self.site_url]:
            parsed = urlparse(value)
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.netloc
                or parsed.path not in {"", "/"}
            ):
                raise ValueError("Site and frontend URLs must be HTTP(S) origins")
        if self.app_env == "production":
            if (
                "secret_key" not in self.model_fields_set
                or len(self.secret_key) < 32
                or self.secret_key.startswith("replace")
            ):
                raise ValueError(
                    "Production requires a random SECRET_KEY of at least 32 characters"
                )
            if not self.site_url.startswith("https://") or not self.frontend_url.startswith(
                "https://"
            ):
                raise ValueError("Production requires HTTPS site and frontend URLs")
            if self.debug:
                raise ValueError("DEBUG must be false in production")
        elif len(self.secret_key) < 32 or self.secret_key.startswith("replace"):
            self.secret_key = secrets.token_urlsafe(48)
        self.telegram_channel_id = self.telegram_channel_id.strip()
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()

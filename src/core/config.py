"""Typed application settings loaded from environment variables.

All configuration enters the process through :class:`Settings`. Nothing else
in the codebase should read ``os.environ`` directly (Master Engineering
Prompt, M002). Secrets (``jwt_secret``, ``database_url``) are never included
in ``repr``/``str`` output.
"""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

ProviderMode = Literal["demo", "live"]
"""(Provider mode flags are consumed by the M022+ provider milestones.)"""


class Settings(BaseSettings):
    """Validated, typed application configuration.

    In ``dev`` mode all fields have safe local defaults. In ``prod`` mode the
    secret-bearing fields are required and their absence raises a clear
    ``ValidationError`` at startup (fail fast, never fall back to a default
    secret).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    env: Literal["dev", "prod"] = "dev"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    jwt_secret: SecretStr | None = None
    jwt_access_ttl_minutes: int = Field(default=15, gt=0)
    jwt_refresh_ttl_days: int = Field(default=7, gt=0)

    database_url: str | None = None

    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]

    # M054 demo seed: unset = dev default (workers/demo_seed refuses that in prod).
    demo_password: SecretStr | None = None

    # M055 hardening: sliding-window limit per bucket per client IP (in-process).
    auth_rate_limit_per_minute: int = Field(default=10, gt=0)
    # M055: mount /docs, /redoc and /openapi.json (M007 status quo; turn off in prod).
    docs_enabled: bool = True

    weather_provider: ProviderMode = "demo"
    satellite_provider: ProviderMode = "demo"
    soil_provider: ProviderMode = "demo"
    disease_provider: ProviderMode = "demo"
    llm_provider: ProviderMode = "demo"

    # M035 image uploads: hard limits for the one untrusted-bytes entry point.
    upload_dir: Path = Path("var/uploads")
    upload_max_bytes: int = Field(default=5 * 1024 * 1024, gt=0)
    upload_max_pixels: int = Field(default=25_000_000, gt=0)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, value: object) -> object:
        """Accept a comma-separated string from env as well as a JSON list."""
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("["):
                return value
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def _require_secrets_in_prod(self) -> Settings:
        """Fail fast and loudly if secrets are missing in production."""
        if self.env == "prod":
            missing: list[str] = []
            if not self.jwt_secret or not self.jwt_secret.get_secret_value():
                missing.append("jwt_secret")
            if not self.database_url:
                missing.append("database_url")
            if missing:
                raise ValueError(
                    "Missing required configuration in prod mode: "
                    + ", ".join(missing)
                    + ". Set them via environment variables; no insecure "
                    "defaults are provided in prod."
                )
        return self


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide, cached settings instance (parsed once)."""
    return Settings()

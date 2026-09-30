"""Unit tests for src.core.config (M002)."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from pydantic import ValidationError
from src.core.config import Settings, get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> Generator[None, None, None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _build_settings() -> Settings:
    """Construct Settings without reading any developer ``.env`` file."""
    return Settings(_env_file=None)  # type: ignore[call-arg]


def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "ENV",
        "LOG_LEVEL",
        "DATABASE_URL",
        "JWT_SECRET",
        "JWT_ACCESS_TTL_MINUTES",
        "JWT_REFRESH_TTL_DAYS",
        "CORS_ORIGINS",
        "WEATHER_PROVIDER",
        "SATELLITE_PROVIDER",
        "SOIL_PROVIDER",
        "DISEASE_PROVIDER",
        "LLM_PROVIDER",
    ):
        monkeypatch.delenv(name, raising=False)


def test_dev_mode_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    _clean_env(monkeypatch)
    settings = _build_settings()
    assert settings.env == "dev"
    assert settings.log_level == "INFO"
    assert settings.jwt_secret is None
    assert settings.database_url is None
    assert settings.jwt_access_ttl_minutes == 15
    assert settings.jwt_refresh_ttl_days == 7
    assert settings.cors_origins == ["http://localhost:5173"]
    assert settings.weather_provider == "demo"
    assert settings.llm_provider == "demo"


def test_ingest_concurrency_default_and_bounds(monkeypatch: pytest.MonkeyPatch) -> None:
    _clean_env(monkeypatch)
    monkeypatch.delenv("INGEST_CONCURRENCY", raising=False)
    assert _build_settings().ingest_concurrency == 4

    with pytest.raises(ValidationError):
        Settings(_env_file=None, ingest_concurrency=0)  # type: ignore[call-arg]


def test_loads_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    _clean_env(monkeypatch)
    monkeypatch.setenv("ENV", "dev")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
    monkeypatch.setenv("JWT_SECRET", "s3cret-value")
    monkeypatch.setenv("CORS_ORIGINS", "http://a.test,http://b.test")
    monkeypatch.setenv("WEATHER_PROVIDER", "live")

    settings = _build_settings()
    assert settings.database_url == "postgresql+asyncpg://u:p@localhost:5432/db"
    assert settings.jwt_secret is not None
    assert settings.jwt_secret.get_secret_value() == "s3cret-value"
    assert settings.cors_origins == ["http://a.test", "http://b.test"]
    assert settings.weather_provider == "live"


def test_prod_missing_secrets_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    _clean_env(monkeypatch)
    monkeypatch.setenv("ENV", "prod")
    with pytest.raises(ValidationError) as exc_info:
        _build_settings()
    message = str(exc_info.value)
    assert "prod mode" in message
    assert "jwt_secret" in message
    assert "database_url" in message


def test_prod_missing_only_jwt_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    _clean_env(monkeypatch)
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
    with pytest.raises(ValidationError) as exc_info:
        _build_settings()
    message = str(exc_info.value)
    assert "jwt_secret" in message
    assert "database_url" not in message


def test_prod_with_secrets_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    _clean_env(monkeypatch)
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
    monkeypatch.setenv("JWT_SECRET", "a-long-random-production-secret")
    settings = _build_settings()
    assert settings.env == "prod"
    assert settings.jwt_secret is not None


def test_blank_jwt_secret_is_treated_as_missing_in_prod(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clean_env(monkeypatch)
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
    monkeypatch.setenv("JWT_SECRET", "")
    with pytest.raises(ValidationError):
        _build_settings()


def test_secret_never_appears_in_repr(monkeypatch: pytest.MonkeyPatch) -> None:
    _clean_env(monkeypatch)
    monkeypatch.setenv("JWT_SECRET", "super-secret-do-not-log")
    settings = _build_settings()
    assert "super-secret-do-not-log" not in repr(settings)
    assert "super-secret-do-not-log" not in str(settings)


def test_get_settings_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    _clean_env(monkeypatch)
    first = get_settings()
    second = get_settings()
    assert first is second

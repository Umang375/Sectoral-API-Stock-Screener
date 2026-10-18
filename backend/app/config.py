"""Application configuration via Pydantic Settings.

WHY Pydantic Settings?
- Validates env vars at startup — crashes fast on missing/wrong values instead of
  failing silently at runtime deep inside a request handler.
- Provides typed access so IDE auto-complete and mypy work out of the box.
- Supports .env files natively, keeping secrets out of source control.

The singleton pattern (lru_cache) ensures we parse the environment exactly once
and reuse the same Settings object across the entire process lifetime.
"""

from functools import lru_cache
import json
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration read from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Core infrastructure ──────────────────────────────────────────────
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    GEMINI_API_KEY: str
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        """Parse CORS origins from a comma-separated string, JSON list, or list."""
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            if v.startswith("[") and v.endswith("]"):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except json.JSONDecodeError:
                    pass
            return [item.strip() for item in v.split(",") if item.strip()]
        if isinstance(v, list):
            return [str(item).strip() for item in v if str(item).strip()]
        return v

    # ── Gemini LLM settings ──────────────────────────────────────────────
    # Using gemini-3.8-flash
    GEMINI_MODEL: str = "gemini-3.8-flash"
    GEMINI_RPM: int = 10  # requests per minute
    GEMINI_RPD: int = 1400  # requests per day
    TAG_BATCH_SIZE: int = 30  # Number of stocks to send per Gemini API call

    # ── Chartlink scraper settings ───────────────────────────────────────
    CHARTLINK_BASE_URL: str = "https://chartink.com"
    CHARTLINK_DELAY_SECONDS: float = 2.0  # polite delay between scrapes

    # ── Tag / snapshot lifecycle ─────────────────────────────────────────
    TAG_CACHE_TTL_SECONDS: int = 604_800  # 7 days
    TAG_CHANGE_THRESHOLD: float = 0.05  # 5 % — triggers a re-tag
    SNAPSHOT_RETENTION_DAYS: int = 365  # 1 year retention policy for daily snapshots and charts

    def model_post_init(self, __context: object) -> None:
        """Fix DATABASE_URL scheme for Render compatibility.

        Render provides postgres:// but asyncpg requires postgresql+asyncpg://.
        This runs after Pydantic validates all fields.
        """
        if self.DATABASE_URL.startswith("postgres://"):
            object.__setattr__(
                self,
                "DATABASE_URL",
                self.DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1),
            )
        elif self.DATABASE_URL.startswith("postgresql://"):
            object.__setattr__(
                self,
                "DATABASE_URL",
                self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1),
            )


@lru_cache
def get_settings() -> Settings:
    """Return a process-wide singleton Settings instance.

    Using @lru_cache so the .env file is read and validated exactly once;
    every subsequent call returns the cached object.
    """
    return Settings()  # type: ignore[call-arg]

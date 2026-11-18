"""Configuration management for OpenSource Radar using Pydantic Settings."""

from functools import lru_cache
import os
from pathlib import Path
from typing import Literal, Optional
from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for resolving relative paths like sqlite:///data/...
BASE_DIR = Path(__file__).resolve().parent

# Ensure .env is loaded
load_dotenv(dotenv_path=BASE_DIR / ".env", override=False)


class Settings(BaseSettings):
    """Application settings with strong validation and secret protection."""

    # Application Environment
    APP_ENV: Literal["development", "production", "test"] = "development"
    APP_NAME: str = "OpenSource Radar"
    LOG_LEVEL: str = "INFO"

    # GitHub Configuration
    GITHUB_TOKEN: Optional[str] = Field(default=None, description="GitHub Personal Access Token")
    GITHUB_API_BASE: str = Field(default="https://api.github.com", description="GitHub REST API Base URL")
    GITHUB_REQUEST_TIMEOUT: int = Field(default=15, description="Timeout in seconds for GitHub API requests")
    GITHUB_MAX_RETRIES: int = Field(default=3, description="Maximum retry attempts on transient failures")

    # AI Provider Configuration (Optional)
    AI_PROVIDER: Literal["openai", "gemini", "none"] = Field(default="openai", description="Active AI provider")
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API Key")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", description="OpenAI model identifier")
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API Key")
    GEMINI_MODEL: str = Field(default="gemini-1.5-flash", description="Gemini model identifier")

    # Persistence
    DATABASE_URL: str = Field(
        default="sqlite:///data/opensource_radar.db",
        description="SQLAlchemy database connection string",
    )

    # Cache & Rate Limiting
    CACHE_TTL_SECONDS: int = Field(default=3600, description="TTL in seconds for cache entries")
    RATE_LIMIT_PER_MINUTE: int = Field(default=30, description="Safety throttle limit for public API requests")

    # Notifications (Optional)
    TELEGRAM_BOT_TOKEN: Optional[str] = Field(default=None, description="Telegram Bot Token for notifications")
    TELEGRAM_CHAT_ID: Optional[str] = Field(default=None, description="Telegram Chat ID for notifications")
    TELEGRAM_ALERT_SCORE_THRESHOLD: int = Field(default=75, description="Opportunity score threshold to trigger Telegram alert")

    # Scheduler & Historical Snapshots
    SNAPSHOT_MIN_INTERVAL_MINUTES: int = Field(default=60, description="Minimum interval between historical snapshots")

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def resolve_sqlite_path(cls, v: str) -> str:
        """Resolve relative SQLite paths to absolute paths under BASE_DIR."""
        if v.startswith("sqlite:///") and not v.startswith("sqlite:////"):
            rel_path = v.replace("sqlite:///", "")
            if not os.path.isabs(rel_path):
                abs_db_path = BASE_DIR / rel_path
                abs_db_path.parent.mkdir(parents=True, exist_ok=True)
                return f"sqlite:///{abs_db_path.as_posix()}"
        return v

    @staticmethod
    def _mask_secret(secret: Optional[str], visible_prefix: int = 4, visible_suffix: int = 4) -> str:
        """Return a safely masked string representing a secret."""
        if not secret:
            return "Not Configured"
        clean = secret.strip()
        if len(clean) <= (visible_prefix + visible_suffix):
            return "●" * len(clean)
        return f"{clean[:visible_prefix]}●●●●{clean[-visible_suffix:]}"

    @property
    def has_github_token(self) -> bool:
        """Check if a non-empty GitHub token is configured."""
        return bool(self.GITHUB_TOKEN and self.GITHUB_TOKEN.strip())

    @property
    def masked_github_token(self) -> str:
        """Safe masked display of GitHub token for UI."""
        return self._mask_secret(self.GITHUB_TOKEN, visible_prefix=4, visible_suffix=3)

    @property
    def has_openai_credentials(self) -> bool:
        """Check if OpenAI API key is set."""
        return bool(self.OPENAI_API_KEY and self.OPENAI_API_KEY.strip())

    @property
    def masked_openai_key(self) -> str:
        """Safe masked display of OpenAI key."""
        return self._mask_secret(self.OPENAI_API_KEY, visible_prefix=3, visible_suffix=3)

    @property
    def has_gemini_credentials(self) -> bool:
        """Check if Gemini API key is set."""
        return bool(self.GEMINI_API_KEY and self.GEMINI_API_KEY.strip())

    @property
    def masked_gemini_key(self) -> str:
        """Safe masked display of Gemini key."""
        return self._mask_secret(self.GEMINI_API_KEY, visible_prefix=4, visible_suffix=3)

    @property
    def has_telegram_credentials(self) -> bool:
        """Check if Telegram notification credentials are set."""
        return bool(self.TELEGRAM_BOT_TOKEN and self.TELEGRAM_CHAT_ID)

    @property
    def masked_telegram_token(self) -> str:
        """Safe masked display of Telegram token."""
        return self._mask_secret(self.TELEGRAM_BOT_TOKEN, visible_prefix=4, visible_suffix=3)

    def __repr__(self) -> str:
        """Ensure secrets are never revealed in string representations."""
        return (
            f"<Settings APP_NAME='{self.APP_NAME}' "
            f"GITHUB_TOKEN='{self.masked_github_token}' "
            f"AI_PROVIDER='{self.AI_PROVIDER}' "
            f"DATABASE_URL='{self.DATABASE_URL}'>"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached singleton application settings."""
    return Settings()

"""
Application configuration using Pydantic Settings.

All configuration is loaded from environment variables with sensible defaults
for local development. In production, these are injected via the container
orchestration platform (Kubernetes secrets, AWS Secrets Manager, etc.).

Never hardcode secrets here. Every sensitive value has no default and will
raise a validation error if missing.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """
    Central configuration for the Knowledge Factory backend.

    Environment variables are loaded from a .env file (if present) and can
    be overridden by the runtime environment. Variable names are uppercased
    versions of the field names below (e.g. DATABASE_URL, REDIS_URL).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Application ───────────────────────────────────────────────
    APP_NAME: str = "Knowledge Factory"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    # Allowed origins for CORS — comma-separated in production
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # ── Database ───────────────────────────────────────────────────
    # PostgreSQL connection string. Format:
    #   postgresql+asyncpg://<user>:<password>@<host>:<port>/<dbname>
    DATABASE_URL: str = "postgresql+asyncpg://kf_user:kf_password@localhost:5432/knowledge_factory"
    # Pool size for the SQLAlchemy connection pool
    DB_POOL_SIZE: int = 20
    # Maximum overflow beyond pool_size
    DB_MAX_OVERFLOW: int = 10
    # Echo SQL statements (only use in development)
    DB_ECHO: bool = False

    # ── Redis ──────────────────────────────────────────────────────
    # Used as Celery broker, result backend, rate-limiting store,
    # and application cache.
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT / Security ─────────────────────────────────────────────
    # RS256 private key for signing access tokens (PEM format).
    # In production, loaded from AWS Secrets Manager or Kubernetes secret.
    JWT_PRIVATE_KEY: str = ""
    # RS256 public key for verifying tokens.
    JWT_PUBLIC_KEY: str = ""
    # Access token time-to-live in minutes.
    JWT_ACCESS_TTL_MINUTES: int = 15
    # Refresh token time-to-live in days.
    JWT_REFRESH_TTL_DAYS: int = 7

    # ── AI / LLM ──────────────────────────────────────────────────
    # Anthropic API key for Claude integration.
    ANTHROPIC_API_KEY: str = ""
    # Default model identifier for AI calls.
    AI_MODEL: str = "claude-sonnet-4-5"
    # Per-cycle spending cap in USD.
    AI_DAILY_SPEND_CAP_USD: float = 50.0

    # ── Code Execution Sandbox ─────────────────────────────────────
    # Judge0 or Piston endpoint URL.
    SANDBOX_URL: str = "http://localhost:2358"
    SANDBOX_API_KEY: str = ""

    # ── Object Storage (S3-compatible) ─────────────────────────────
    S3_BUCKET_NAME: str = "knowledge-factory"
    S3_REGION: str = "us-east-1"
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""

    # ── Email ──────────────────────────────────────────────────────
    # SES or SendGrid configuration.
    EMAIL_FROM_ADDRESS: str = "noreply@knowledgefactory.io"
    SENDGRID_API_KEY: str = ""

    # ── Proctoring ─────────────────────────────────────────────────
    # Maximum proctoring warnings before assessment termination.
    PROCTORING_MAX_WARNINGS: int = 3
    # Interval (seconds) between client-side proctoring event batches.
    PROCTORING_EVENT_INTERVAL_SECONDS: int = 5


@lru_cache
def get_settings() -> Settings:
    """
    Cached accessor for the Settings singleton.

    Using lru_cache ensures the .env file is parsed only once per process.
    FastAPI dependencies can call get_settings() without paying the parse
    cost on every request.
    """
    return Settings()

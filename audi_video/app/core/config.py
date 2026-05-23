"""
Core configuration module for the AI Proctoring Backend.

All settings are loaded from environment variables (with documented defaults)
using pydantic-settings. A `.env` file is also supported for local development.
"""

from __future__ import annotations

import functools
from typing import List, Union
from pydantic import field_validator

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Application configuration loaded from environment variables.
    """
    # --- Required ---
    OPENROUTER_API_KEY: str

    # --- Optional with defaults ---
    LOG_LEVEL: str = "INFO"
    MAX_AUDIO_SIZE_MB: int = 20
    YOLO_CONFIDENCE: float = 0.35
    ENABLE_GPU: bool = False
    WORKER_POOL_SIZE: int = 4
    CORS_ORIGINS: Union[str, List[str]] = ["*"]
    MAIN_BACKEND_URL: str = "http://127.0.0.1:8000"
    PROCTORING_JWT_SECRET: str = "dev-proctoring-secret-stable"
    JWT_SECRET_KEY: str = "dev-stable-secret-change-in-production"

    # --- HuggingFace cache isolation ---
    HF_MODULES_CACHE: str | None = None

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def split_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("["): # Handle potential JSON
                import json
                return json.loads(v)
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }



@functools.lru_cache(maxsize=1)
def get_config() -> Config:
    """Return the application Config singleton.

    The result is cached after the first call so that environment variables
    and the `.env` file are parsed exactly once per process lifetime.

    Returns:
        Config: The populated configuration object.

    Raises:
        pydantic.ValidationError: If OPENROUTER_API_KEY is missing or any
            field value cannot be coerced to its declared type.
    """
    return Config()

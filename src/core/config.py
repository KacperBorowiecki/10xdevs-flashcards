import os
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Supabase Configuration
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: Optional[str] = None

    # Application Configuration
    app_secret_key: str
    app_env: str = "development"

    # Auth Configuration
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # OpenRouter/LLM Configuration
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_MODEL: str = "google/gemma-3-27b-it"
    LLM_TIMEOUT: int = 30
    LLM_MAX_TOKENS: int = 2000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra environment variables
    )


# Create global settings instance
settings = Settings()


# Helper function to check if we're in development
def is_development() -> bool:
    """Check if application is running in development mode."""
    return settings.app_env == "development"


# Legacy compatibility - deprecated, use settings instance instead

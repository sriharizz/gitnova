"""
GitNova v4.2 — Application Configuration

All environment variables are read here with Pydantic Settings.
Never use os.getenv() anywhere else in the codebase — import settings instead.

Usage:
    from app.core.config import settings
    print(settings.database_url)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = ""
    supabase_url: str = ""
    supabase_key: str = ""

    # ── LLM Providers ─────────────────────────────────────────────────────────
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"
    gemini_fallback_model: str = "gemini-3.5-flash-lite"
    gemini_rpm_limit: int = 15
    gemini_input_tpm_limit: int = 1000000
    gemini_rpd_limit: int = 1500
    groq_api_key: str = ""
    openrouter_api_key: str = ""
    nvidia_api_key: str = ""
    nvidia_model: str = "poolside/laguna-xs-2.1"
    llm_provider: str = "gemini"
    llm_model: str = "gemini-3.5-flash"
    llm_fallback_provider: str = "gemini"
    llm_fallback_model: str = "gemini-3.5-flash-lite"
    secondary_fallback_provider: str = "groq"

    # ── GitHub ────────────────────────────────────────────────────────────────
    github_token: str = ""

    # ── App ───────────────────────────────────────────────────────────────────
    app_env: str = "development"        # development | production
    log_level: str = "INFO"
    api_version: str = "4.2.0"

    # ── Pipeline ──────────────────────────────────────────────────────────────
    # How many repos to discover per weekly qualification run
    repos_per_run: int = 100
    # Minimum score for a repo to be stored as active
    min_score_threshold: float = 40.0

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def has_database(self) -> bool:
        return bool(self.database_url)

    @property
    def has_groq(self) -> bool:
        return bool(self.groq_api_key)

    @property
    def has_github(self) -> bool:
        return bool(self.github_token)


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings instance. Called once, reused everywhere.
    Use this function instead of instantiating Settings directly.
    """
    return Settings()


# Module-level singleton — import this directly
settings = get_settings()

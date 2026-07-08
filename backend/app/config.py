# Shared config — env-backed settings. Change only by team agreement.
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central settings, loaded from environment / backend/.env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    city: str = "Delhi"
    env: str = "development"
    log_level: str = "info"

    # Infra (Person A)
    database_url: str = "postgresql://airintel:airintel@localhost:5432/airintel"
    redis_url: str = "redis://localhost:6379/0"

    # External data (Person A)
    openaq_api_key: str = ""

    # LLM providers (Person C)
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    kimi_api_key: str = ""

    # CORS
    frontend_origin: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()

from pathlib import Path
from functools import lru_cache
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load backend/.env using absolute path relative to this file
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)


class Settings(BaseSettings):
    """Central settings, loaded from environment / backend/.env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    city: str = "Delhi"
    env: str = "development"
    log_level: str = "info"

    # Infra (Person A)
    database_url: str = "postgresql://airpulse:airpulse@localhost:5432/airpulse"
    redis_url: str = "redis://localhost:6379/0"

    # External data (Person A)
    openaq_api_key: str = ""

    # LLM providers (Person C)
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    kimi_api_key: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"

    # CORS
    frontend_origin: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()

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
    database_url: str = "postgresql://airpulse:airpulse@localhost:5432/airpulse"
    redis_url: str = "redis://localhost:6379/0"

    POSTGRES_USER: str = "airpulse"
    POSTGRES_PASSWORD: str = "airpulse"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "airpulse"

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        # If database_url is provided, use it and ensure it has +asyncpg
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql+asyncpg://"):
            pass
        else:
            # Fallback to individual components
            import os
            user = os.getenv("POSTGRES_USER", self.POSTGRES_USER)
            password = os.getenv("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
            server = os.getenv("POSTGRES_SERVER", self.POSTGRES_SERVER)
            port = os.getenv("POSTGRES_PORT", self.POSTGRES_PORT)
            db = os.getenv("POSTGRES_DB", self.POSTGRES_DB)
            url = f"postgresql+asyncpg://{user}:{password}@{server}:{port}/{db}"
        return url

    @property
    def REDIS_URL(self) -> str:
        import os
        return os.getenv("REDIS_URL", self.redis_url)

    # External data (Person A)
    openaq_api_key: str = ""

    # LLM providers (Person C)
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    kimi_api_key: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"  # NOTE: "gemini-3.5-flash" does not exist

    # CORS
    frontend_origin: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()


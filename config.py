"""
TravelPilot — Central Configuration
Loads all settings from environment variables / .env file.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── Gemini ────────────────────────────────────────
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"

    # ── Tavily ────────────────────────────────────────
    tavily_api_key: str = ""

    # ── OpenWeather ───────────────────────────────────
    openweather_api_key: str = ""

    # ── Database ──────────────────────────────────────
    database_url: str = "postgresql+asyncpg://username:password@localhost:5432/travelpilot"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "database"
    postgres_user: str = "username"
    postgres_password: str = "password"

    # ── App ───────────────────────────────────────────
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = True
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    # ── Trip Settings ─────────────────────────────────
    default_currency: str = "INR"
    max_trip_days: int = 30

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# Singleton instance used across the app
settings = get_settings()

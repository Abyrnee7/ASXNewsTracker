from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "ASX News Reaction"
    database_url: str = "sqlite:///./asx_reactions.db"

    @property
    def sqlalchemy_database_url(self) -> str:
        # Some hosts expose Postgres URLs as postgres://, while SQLAlchemy expects postgresql://.
        if self.database_url.startswith("postgres://"):
            return "postgresql://" + self.database_url[len("postgres://"):]
        return self.database_url

    # Comma-separated ASX ticker list. Examples: BHP,CBA,JBH,WDS,FMG,CSL
    watchlist: str = "BHP,CBA,JBH,WDS"

    # Demo/free providers. For production, swap providers in app/services/ingestion.py.
    enable_asx_public_announcements: bool = True
    enable_gdelt_news: bool = True
    price_provider: str = "yfinance"

    # Scheduler
    scheduler_enabled: bool = True
    scheduler_hour: int = 0
    scheduler_minute: int = 5

    # Analysis window
    event_window_hours: int = 24
    intraday_interval: str = "5m"

    # CORS
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def watchlist_codes(self) -> list[str]:
        return [c.strip().upper() for c in self.watchlist.split(",") if c.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

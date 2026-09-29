"""Application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "DataForge Analytics API"
    api_prefix: str = "/api/v1"
    debug: bool = False

    # Local data directory (overridden by Tauri / DATAFORGE_DATA_DIR)
    data_dir: Path = Path("./data")
    host: str = "127.0.0.1"
    port: int = 8000

    database_url: str = "sqlite+aiosqlite:///./data/dataforge.db"

    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "tauri://localhost",
        "https://tauri.localhost",
        "http://tauri.localhost",
        "https://asset.localhost",
        "http://asset.localhost",
    ]

    default_page_size: int = 100
    max_page_size: int = 1000
    preview_rows: int = 50
    chunk_size: int = 50_000

    mock_auth_enabled: bool = True
    mock_auth_token: str = "demo-token"

    seed_demo_on_startup: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


def ensure_data_dirs(settings: Settings | None = None) -> Path:
    s = settings or get_settings()
    base = s.data_dir.resolve()
    for sub in ("datasets", "uploads", "exports", "cache"):
        (base / sub).mkdir(parents=True, exist_ok=True)
    return base

from functools import lru_cache
import json
from pathlib import Path
from typing import Any, List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve path to backend root directory where .env is located
BACKEND_DIR = Path(__file__).resolve().parents[2]
WORKSPACE_DIR = BACKEND_DIR.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and backend/.env."""

    # Project Information
    app_name: str = "NEREUS API"
    app_version: str = "1.0.0"
    app_description: str = "NEREUS — Scientific Ocean-Data Visualization & Analysis API"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_database_url(cls, v: Any) -> str:
        """Normalize PostgreSQL connection URLs to explicitly use psycopg 3 driver."""
        if isinstance(v, str):
            url = v.strip()
            # If scheme is postgres:// (common in Heroku/Render/Supabase) or postgresql://
            # without an explicit driver (+psycopg, +psycopg2, +asyncpg), normalize to postgresql+psycopg://
            if url.startswith("postgres://"):
                return "postgresql+psycopg://" + url[len("postgres://"):]
            elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
                return "postgresql+psycopg://" + url[len("postgresql://"):]
            return url
        return v

    # Storage and Data Directory
    data_root: str = "data"

    # CORS Configuration
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "https://nereus-sih.vercel.app",
    ]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        """Support JSON string arrays, comma-separated lists, or direct Python lists."""
        if isinstance(v, str):
            v_trimmed = v.strip()
            if v_trimmed.startswith("[") and v_trimmed.endswith("]"):
                try:
                    return json.loads(v_trimmed)
                except Exception:
                    pass
            return [origin.strip() for origin in v_trimmed.split(",") if origin.strip()]
        elif isinstance(v, list):
            return [str(origin).strip() for origin in v if str(origin).strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Cached settings factory to prevent redundant file I/O."""
    return Settings()

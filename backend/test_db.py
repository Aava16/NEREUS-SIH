from pathlib import Path

from sqlalchemy import create_engine, text
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    database_url: str

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
    )


settings = Settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)


with engine.connect() as connection:
    result = connection.execute(
        text(
            """
            SELECT
                current_database() AS database_name,
                current_user AS database_user,
                version() AS postgres_version
            """
        )
    )

    row = result.one()

    print("Database:", row.database_name)
    print("User:", row.database_user)
    print("PostgreSQL:", row.postgres_version)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5434/db_plan_nutricional"
    app_env: str = "development"
    log_level: str = "INFO"


settings = Settings()

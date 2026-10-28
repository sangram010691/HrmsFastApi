"""Values are loaded from backend/.env. Never commit real secrets."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://hospital_user:local_development_only@localhost:5432/hospital_erp"
    jwt_secret: str = ""  # required at startup
    token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:5173"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "SmartEvent Platform"
    APP_ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./smart_event.db"
    JWT_SECRET_KEY: str = "9f82d8c36b8a21f763989c72e45bbd780ef468c8bfae829370144fbc71d530e2"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    FRONTEND_URL: str = "http://localhost:5173"
    EVENT_REMINDER_HOURS_AHEAD: int = 48

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

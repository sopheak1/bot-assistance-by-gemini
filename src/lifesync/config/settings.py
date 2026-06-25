import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "local"
    BOT_TOKEN: str = ""
    BOT_MODE: str = "polling"
    LOG_LEVEL: str = "INFO"
    DATA_DIR: str = "./data"
    BOT_DB_PATH: str = "./data/bot.db"
    USER_DB_DIR: str = "./data/users"
    DEFAULT_TIMEZONE: str = "Asia/Phnom_Penh"
    DEFAULT_STANDUP_HOUR: int = 9
    DEFAULT_ROLLOVER_HOUR: int = 2
    SENTRY_DSN: str = ""
    HTTP_PROXY: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()

# Ensure directories exist
os.makedirs(settings.DATA_DIR, exist_ok=True)
os.makedirs(settings.USER_DB_DIR, exist_ok=True)

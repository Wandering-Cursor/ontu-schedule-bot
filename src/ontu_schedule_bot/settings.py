"""This module loads (or sets) secrets for the bot (API_TOKEN, API_URL...)"""

import pydantic
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
    )

    BOT_TOKEN: pydantic.SecretStr = pydantic.Field(
        min_length=1,
    )

    API_URL: pydantic.HttpUrl
    API_USERNAME: str = pydantic.Field(
        min_length=1,
    )
    API_PASSWORD: pydantic.SecretStr = pydantic.Field(
        min_length=1,
    )

    DEBUG_CHAT_ID: int

    LOG_DIR: str = "/tmp/ontu_schedule_bot_logs"
    PERSISTENCE_FILEPATH: str = "/tmp/ontu_schedule_bot_persistence"

    WEBHOOK_URL: pydantic.HttpUrl | None = None
    RUN_PERIODIC_JOBS: bool = True


settings = Settings()  # pyright: ignore[reportCallIssue]

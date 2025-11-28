"""This module loads (or sets) secrets for the bot (API_TOKEN, API_URL...)"""

import pydantic
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
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


settings = Settings()

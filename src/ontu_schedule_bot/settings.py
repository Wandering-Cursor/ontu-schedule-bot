"""This module loads (or sets) secrets for the bot (API_TOKEN, API_URL...)"""

import pydantic
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BOT_TOKEN: str

    API_URL: pydantic.HttpUrl
    API_USERNAME: str
    API_PASSWORD: pydantic.SecretStr

    DEBUG_CHAT_ID: int

settings = Settings()

"""This module loads (or sets) secrets for the bot (API_TOKEN, API_URL...)"""

import pydantic
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_TOKEN: str
    API_URL: pydantic.HttpUrl
    DEBUG_CHAT_ID: int

settings = Settings()

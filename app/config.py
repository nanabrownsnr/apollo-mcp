"""Configuration for Apollo.io API."""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Apollo.io API Configuration
    APOLLO_API_KEY: str
    APOLLO_BASE_URL: str = "https://api.apollo.io/v1"

    # Rate limiting (optional)
    MAX_RETRIES: int = 3
    TIMEOUT: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

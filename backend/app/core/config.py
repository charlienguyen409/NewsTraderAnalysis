from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    database_url: str
    redis_url: str
    openai_api_key: str
    anthropic_api_key: str
    secret_key: str
    max_positions: int = 10
    min_confidence: float = 0.7
    scraping_rate_limit: int = 10
    
    class Config:
        # Look for .env file in project root
        env_file = Path(__file__).parent.parent.parent.parent / ".env"
        extra = "ignore"  # Ignore extra fields like VITE_* variables


settings = Settings()
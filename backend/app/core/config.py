from pydantic_settings import BaseSettings
from typing import Optional


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
        env_file = ".env"


settings = Settings()
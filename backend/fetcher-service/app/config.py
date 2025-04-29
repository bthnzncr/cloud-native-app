from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os

class Settings(BaseSettings):
    # RabbitMQ settings
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int
    RABBITMQ_DEFAULT_USER: str
    RABBITMQ_DEFAULT_PASS: str
    RABBITMQ_QUEUE: str

    # Application settings
    FETCH_INTERVAL_MINUTES: int
    
    # RSS feeds - will be parsed from comma-separated string in .env
    RSS_FEEDS_STRING: str
    
    @property
    def RSS_FEEDS(self) -> List[str]:
        """Parse the RSS feeds from the environment string."""
        return [feed.strip() for feed in self.RSS_FEEDS_STRING.split(",") if feed.strip()]

    model_config = SettingsConfigDict(
        env_file_encoding='utf-8'
    )

settings = Settings() 
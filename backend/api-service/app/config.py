import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # MongoDB settings
    MONGO_URI: str
    DB_NAME: str
    ARTICLE_COLLECTION: str
    
    # API settings
    API_TITLE: str = "News Aggregator API"
    API_DESCRIPTION: str = "API for retrieving news articles from the aggregator database"
    API_VERSION: str = "1.0.0"
    
    # Default pagination values
    DEFAULT_LIMIT: int = 20
    MAX_LIMIT: int = 100

    # Use the new configuration format for pydantic v2
    model_config = SettingsConfigDict(
        env_file=".env" if os.path.exists(".env") else None,
        env_file_encoding='utf-8'
    )

# Create settings instance
settings = Settings() 
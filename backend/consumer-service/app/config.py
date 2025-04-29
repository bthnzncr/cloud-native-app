from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    # MongoDB settings
    MONGO_URI: str
    DB_NAME: str
    ARTICLE_COLLECTION: str

    # RabbitMQ settings
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int
    RABBITMQ_DEFAULT_USER: str
    RABBITMQ_DEFAULT_PASS: str
    RABBITMQ_QUEUE: str
    
    # Similarity threshold for duplicate detection
    SIMILARITY_THRESHOLD: float
    
    # Deduplication window in hours
    DEDUPLICATION_WINDOW_HOURS: int

    # Use the new configuration format for pydantic v2
    model_config = SettingsConfigDict(
        env_file=".env" if os.path.exists(".env") else None,
        env_file_encoding='utf-8'
    )

settings = Settings() 
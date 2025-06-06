from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Dict, Optional, ClassVar
import os

# Define feed information structure
class FeedInfo:
    def __init__(self, url: str, provider: str):
        self.url = url
        self.provider = provider  # BBC, CNN, etc.

class Settings(BaseSettings):
    # RabbitMQ settings
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int
    RABBITMQ_DEFAULT_USER: str
    RABBITMQ_DEFAULT_PASS: str
    RABBITMQ_QUEUE: str

    # Application Info (for health check)
    VERSION: Optional[str] = "0.1.0"
    ENVIRONMENT: Optional[str] = "development"

    
    @property
    def FEED_CONFIGURATIONS(self) -> List[FeedInfo]:
        return [
            # BBC News feeds
            FeedInfo("https://feeds.bbci.co.uk/news/rss.xml", "BBC News"),
            FeedInfo("https://feeds.bbci.co.uk/news/technology/rss.xml", "BBC News"),
            FeedInfo("https://feeds.bbci.co.uk/news/business/rss.xml", "BBC News"),
            FeedInfo("https://feeds.bbci.co.uk/news/politics/rss.xml", "BBC News"),
            FeedInfo("https://feeds.bbci.co.uk/news/science_and_environment/rss.xml", "BBC News"),
            FeedInfo("https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml", "BBC News"),
            FeedInfo("https://feeds.bbci.co.uk/news/health/rss.xml", "BBC News"),
            
            # CNN feeds
            FeedInfo("http://rss.cnn.com/rss/edition.rss", "CNN"),
            FeedInfo("http://rss.cnn.com/rss/edition_technology.rss", "CNN"),
            FeedInfo("http://rss.cnn.com/rss/edition_business.rss", "CNN"),
            FeedInfo("http://rss.cnn.com/rss/cnn_allpolitics.rss", "CNN"),
            FeedInfo("http://rss.cnn.com/rss/edition_space.rss", "CNN"),
            FeedInfo("http://rss.cnn.com/rss/edition_entertainment.rss", "CNN"),
            
            # New York Times feeds
            FeedInfo("https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "New York Times"),
            FeedInfo("https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml", "New York Times"),
            FeedInfo("https://rss.nytimes.com/services/xml/rss/nyt/Business.xml", "New York Times"),
            FeedInfo("https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml", "New York Times"),
            FeedInfo("https://rss.nytimes.com/services/xml/rss/nyt/Science.xml", "New York Times"),
            
       
            # Washington Post feeds
            FeedInfo("http://feeds.washingtonpost.com/rss/world", "Washington Post"),
                        
            
            # Financial Times feed
            FeedInfo("https://www.ft.com/world?format=rss", "Financial Times"),
            
            # Independent feed
            FeedInfo("https://www.independent.co.uk/news/world/rss", "Independent"),
        ]

settings = Settings() 
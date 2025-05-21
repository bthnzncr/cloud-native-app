from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any

class Article(BaseModel):
    source: str = Field(..., description="Source of the news article (e.g., website name)")
    title: str = Field(..., description="Title of the news article")
    description: Optional[str] = Field(None, description="Short description or summary of the article")
    link: HttpUrl = Field(..., description="Direct link to the full article")
    published_date: Optional[datetime] = Field(None, description="Publication date of the article")
    category: Optional[str] = Field(None, description="Category or topic of the article")
    source_category: Optional[str] = Field(None, description="Category defined in the fetcher configuration")
    picture: Optional[HttpUrl] = Field(None, description="URL of an image associated with the article")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source": "Example News",
                "title": "Big Tech Announces New AI Initiative",
                "description": "A groundbreaking AI project aims to solve major world problems.",
                "link": "http://example.com/news/123",
                "published_date": "2024-01-15T10:00:00Z",
                "category": "Technology",
                "picture": "http://example.com/images/ai_initiative.jpg"
            }
        }
    )
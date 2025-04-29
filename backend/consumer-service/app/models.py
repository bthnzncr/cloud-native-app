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

class ArticleResponse(BaseModel):
    """Model for article response."""
    _id: str = Field(..., description="MongoDB ObjectId as string")
    source: str = Field(..., description="Source of the article")
    title: str = Field(..., description="Title of the article")
    description: Optional[str] = Field(None, description="Description or summary of the article")
    link: str = Field(..., description="Link to the original article")
    published_date: datetime = Field(..., description="Publication date of the article")
    category: Optional[str] = Field(None, description="Category of the article")
    picture: Optional[str] = Field(None, description="URL to article image/thumbnail")
    fetched_at: datetime = Field(..., description="When the article was fetched by the system")

    model_config = ConfigDict(
        extra="allow"
    )

class ErrorResponse(BaseModel):
    """Model for error responses."""
    detail: str

class CategoryResponse(BaseModel):
    """Model for category response."""
    name: str
    count: int

class SourceResponse(BaseModel):
    """Model for source response."""
    name: str
    count: int

# If needed for future use:
class ArticleCreate(BaseModel):
    """Model for creating an article (if you add this functionality)."""
    source: str
    title: str
    description: Optional[str] = None
    link: str
    published_date: datetime
    category: Optional[str] = None
    picture: Optional[str] = None 
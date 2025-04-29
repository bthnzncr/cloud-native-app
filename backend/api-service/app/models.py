from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, HttpUrl

class Article(BaseModel):
    """Base article model."""
    id: str = Field(..., description="MongoDB ObjectId as string", alias="_id")
    source: str = Field(..., description="Source of the news article")
    title: str = Field(..., description="Title of the news article")
    description: Optional[str] = Field(None, description="Short description or summary")
    link: str = Field(..., description="Direct link to the full article")
    published_date: datetime = Field(..., description="Publication date of the article")
    category: Optional[str] = Field(None, description="Category or topic of the article")
    picture: Optional[str] = Field(None, description="URL of image associated with article")
    fetched_at: datetime = Field(..., description="When the article was fetched by the system")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "60d21b4967d0d8992e610c85",
                "source": "BBC News",
                "title": "New climate agreement reached at global summit",
                "description": "Countries agree to reduce carbon emissions by 50% by 2030.",
                "link": "https://example.com/news/climate-agreement",
                "published_date": "2024-01-15T10:00:00Z",
                "category": "Environment",
                "picture": "https://example.com/images/climate.jpg",
                "fetched_at": "2024-01-15T10:30:00Z"
            }
        }

class ArticleList(BaseModel):
    """Response model for a list of articles."""
    total: int = Field(..., description="Total number of matching articles")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Number of items per page")
    articles: List[Article] = Field(..., description="List of article objects")

class CategoryCount(BaseModel):
    """Model for category statistics."""
    name: str = Field(..., description="Category name")
    count: int = Field(..., description="Number of articles in this category")

class SourceCount(BaseModel):
    """Model for source statistics."""
    name: str = Field(..., description="Source name")
    count: int = Field(..., description="Number of articles from this source")

class StatsResponse(BaseModel):
    """Response model for statistics."""
    total_articles: int = Field(..., description="Total number of articles")
    sources: List[SourceCount] = Field(..., description="Source statistics")
    categories: List[CategoryCount] = Field(..., description="Category statistics")

class TimeFilter(BaseModel):
    """Model for time-based filtering parameters."""
    from_date: Optional[datetime] = Field(None, description="Filter articles from this date")
    to_date: Optional[datetime] = Field(None, description="Filter articles until this date")

class QueryParams(BaseModel):
    """Model for query parameters."""
    query: Optional[str] = Field(None, description="Search keywords")
    category: Optional[str] = Field(None, description="Filter by category")
    source: Optional[str] = Field(None, description="Filter by source")
    from_date: Optional[datetime] = Field(None, description="From date")
    to_date: Optional[datetime] = Field(None, description="To date")
    page: int = Field(1, description="Page number")
    limit: int = Field(20, description="Items per page") 
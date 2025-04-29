import logging
import sys
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response, JSONResponse
from fastapi.exception_handlers import http_exception_handler

from .config import settings
from .models import Article, ArticleList, StatsResponse, CategoryCount, SourceCount
from .db import connect_db, close_db, get_article_collection
from . import service

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Create the FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
REQUESTS = Counter("api_requests_total", "Total API requests", ["endpoint", "method"])

# MongoDB client instance
db_client = None

@app.on_event("startup")
async def startup_db_client():
    global db_client
    try:
        # Try to connect to MongoDB with retries
        max_retries = 5
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to connect to MongoDB (attempt {attempt+1}/{max_retries})")
                db_client = await connect_db()
                
                # Test the connection by trying to get the article collection
                collection = get_article_collection(db_client)
                # Verify connection with a simple operation
                await collection.find_one({})
                
                logger.info("MongoDB connection established and verified")
                return  # Success, exit the function
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Failed to connect to MongoDB: {str(e)}. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise  # Re-raise on final attempt
        
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB connection after retries: {str(e)}")
        # Exit the application if MongoDB connection fails
        logger.critical("Exiting application due to database connection failure")
        sys.exit(1)  # Exit with error code

@app.on_event("shutdown")
async def shutdown_db_client():
    if db_client:
        await close_db(db_client)
        logger.info("MongoDB connection closed")

@app.exception_handler(RuntimeError)
async def runtime_exception_handler(request: Request, exc: RuntimeError):
    """Custom exception handler for RuntimeError (like DB connection issues)."""
    logger.error(f"Runtime error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": f"Service error: {str(exc)}"},
    )

@app.get("/metrics", include_in_schema=False)
async def metrics():
    """Endpoint for Prometheus metrics."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/api/articles", response_model=ArticleList)
async def get_articles(
    query: Optional[str] = None,
    category: Optional[str] = None,
    source: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(settings.DEFAULT_LIMIT, ge=1, le=settings.MAX_LIMIT, description="Items per page")
):
    """
    Get articles with optional filtering and pagination.
    - **query**: Optional search term to filter articles by content
    - **category**: Filter articles by category
    - **source**: Filter articles by source
    - **from_date**: Filter articles published after this date (ISO format)
    - **to_date**: Filter articles published before this date (ISO format)
    - **page**: Page number (starts from 1)
    - **limit**: Number of items per page
    """
    REQUESTS.labels(endpoint="/api/articles", method="GET").inc()
    
    try:
        articles, total = await service.get_articles(
            query=query,
            category=category,
            source=source,
            from_date=from_date,
            to_date=to_date,
            page=page,
            limit=limit
        )
        
        return ArticleList(
            total=total,
            page=page,
            limit=limit,
            articles=articles
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting articles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving articles: {str(e)}"
        )

@app.get("/api/articles/{article_id}", response_model=Article)
async def get_article(article_id: str):
    """
    Get a single article by its ID.
    - **article_id**: The ID of the article to retrieve
    """
    REQUESTS.labels(endpoint="/api/articles/{article_id}", method="GET").inc()
    
    try:
        article = await service.get_article_by_id(article_id)
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Article with ID {article_id} not found"
            )
        
        return article
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}"
        )

@app.get("/api/recent", response_model=List[Article])
async def get_recent_articles(
    hours: int = Query(1, ge=1, le=48, description="Hours to look back"),
    limit: int = Query(10, ge=1, le=50, description="Number of articles to return")
):
    """
    Get recent articles published within the specified number of hours.
    - **hours**: Number of hours to look back (1-48)
    - **limit**: Maximum number of articles to return (1-50)
    """
    REQUESTS.labels(endpoint="/api/recent", method="GET").inc()
    
    try:
        articles = await service.get_recent_articles(hours=hours, limit=limit)
        return articles
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}"
        )

@app.get("/api/categories", response_model=List[CategoryCount])
async def get_categories():
    """Get all available categories with article counts."""
    REQUESTS.labels(endpoint="/api/categories", method="GET").inc()
    
    try:
        categories = await service.get_categories()
        return categories
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}"
        )

@app.get("/api/sources", response_model=List[SourceCount])
async def get_sources():
    """Get all available sources with article counts."""
    REQUESTS.labels(endpoint="/api/sources", method="GET").inc()
    
    try:
        sources = await service.get_sources()
        return sources
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}"
        )

@app.get("/api/stats", response_model=StatsResponse)
async def get_statistics():
    """Get overall statistics about the articles in the database."""
    REQUESTS.labels(endpoint="/api/stats", method="GET").inc()
    
    try:
        stats = await service.get_statistics()
        return stats
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy"}

@app.get("/health/db")
async def db_health_check():
    """Database connectivity health check endpoint."""
    try:
        # Get collection
        collection = get_article_collection()
        # Perform a simple database operation
        await collection.find_one({})
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.warning(f"Database health check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            content={"status": "unhealthy", "database": "disconnected", "error": str(e)}
        ) 
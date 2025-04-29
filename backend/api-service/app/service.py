import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pymongo import DESCENDING
from bson import ObjectId
from dateutil.parser import parse

from .db import get_article_collection
from .models import Article, CategoryCount, SourceCount

logger = logging.getLogger(__name__)

async def get_articles(
    query: Optional[str] = None,
    category: Optional[str] = None,
    source: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    page: int = 1,
    limit: int = 20
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Get articles with optional filtering and pagination.
    Returns a tuple of (articles, total_count).
    """
    try:
        article_collection = get_article_collection()
        
        # Build query filter
        filter_query = {}
        
        # Text search
        if query:
            try:
                filter_query["$text"] = {"$search": query}
                # Test if a text index exists by running a count
                await article_collection.count_documents(filter_query)
            except Exception as e:
                logger.warning(f"Text search failed, falling back to regex search: {str(e)}")
                # Fallback to regex search if text index is not available
                search_regex = {"$regex": query, "$options": "i"}
                filter_query = {"$or": [
                    {"title": search_regex},
                    {"description": search_regex},
                    {"category": search_regex}
                ]}
        
        # Category filter
        if category:
            if "$or" in filter_query:  # If we're already using $or for text search
                for condition in filter_query["$or"]:
                    # Add category to each $or condition
                    if "category" not in condition:
                        condition["category"] = {"$regex": category, "$options": "i"}
            else:
                filter_query["category"] = {"$regex": category, "$options": "i"}
        
        # Source filter
        if source:
            if "$or" in filter_query:  # If we're already using $or for text search
                for condition in filter_query["$or"]:
                    # Add source to each $or condition
                    if "source" not in condition:
                        condition["source"] = {"$regex": source, "$options": "i"}
            else:
                filter_query["source"] = {"$regex": source, "$options": "i"}
        
        # Date range filter
        date_filter = {}
        if from_date:
            date_filter["$gte"] = from_date
        if to_date:
            date_filter["$lte"] = to_date
        if date_filter:
            if "$or" in filter_query:  # If we're already using $or for text search
                for condition in filter_query["$or"]:
                    # Add date filter to each $or condition
                    condition["published_date"] = date_filter
            else:
                filter_query["published_date"] = date_filter
        
        # Calculate pagination
        skip = (page - 1) * limit
        
        # Get total count for pagination
        total = await article_collection.count_documents(filter_query)
        
        # Get articles with pagination
        cursor = article_collection.find(filter_query) \
            .sort("published_date", DESCENDING) \
            .skip(skip) \
            .limit(limit)
        
        # Convert MongoDB documents to dictionaries
        articles = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
            articles.append(doc)
        
        return articles, total
    except Exception as e:
        logger.error(f"Error retrieving articles: {e}")
        raise RuntimeError(f"Failed to retrieve articles: {e}")

async def get_article_by_id(article_id: str) -> Optional[Dict[str, Any]]:
    """Get a single article by its ID."""
    try:
        article_collection = get_article_collection()
        
        try:
            article = await article_collection.find_one({"_id": ObjectId(article_id)})
            if article:
                article["_id"] = str(article["_id"])
            return article
        except Exception as e:
            logger.error(f"Error retrieving article {article_id}: {str(e)}")
            return None
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise RuntimeError(f"Failed to retrieve article: {e}")

async def get_recent_articles(hours: int = 1, limit: int = 20) -> List[Dict[str, Any]]:
    """Get articles published within the last specified hours."""
    try:
        article_collection = get_article_collection()
        
        from_date = datetime.utcnow() - timedelta(hours=hours)
        filter_query = {"published_date": {"$gte": from_date}}
        
        cursor = article_collection.find(filter_query) \
            .sort("published_date", DESCENDING) \
            .limit(limit)
        
        articles = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            articles.append(doc)
        
        return articles
    except Exception as e:
        logger.error(f"Error retrieving recent articles: {e}")
        raise RuntimeError(f"Failed to retrieve recent articles: {e}")

async def get_categories() -> List[CategoryCount]:
    """Get list of categories with article counts."""
    try:
        article_collection = get_article_collection()
        
        pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$match": {"_id": {"$ne": None}}},  # Filter out null categories
            {"$sort": {"count": -1}},
            {"$project": {"name": "$_id", "count": 1, "_id": 0}}
        ]
        
        cursor = article_collection.aggregate(pipeline)
        categories = []
        async for doc in cursor:
            categories.append(CategoryCount(**doc))
        
        return categories
    except Exception as e:
        logger.error(f"Error retrieving categories: {e}")
        raise RuntimeError(f"Failed to retrieve categories: {e}")

async def get_sources() -> List[SourceCount]:
    """Get list of sources with article counts."""
    try:
        article_collection = get_article_collection()
        
        pipeline = [
            {"$group": {"_id": "$source", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$project": {"name": "$_id", "count": 1, "_id": 0}}
        ]
        
        cursor = article_collection.aggregate(pipeline)
        sources = []
        async for doc in cursor:
            sources.append(SourceCount(**doc))
        
        return sources
    except Exception as e:
        logger.error(f"Error retrieving sources: {e}")
        raise RuntimeError(f"Failed to retrieve sources: {e}")

async def get_statistics() -> Dict[str, Any]:
    """Get overall statistics about the articles database."""
    try:
        article_collection = get_article_collection()
        
        total = await article_collection.count_documents({})
        categories = await get_categories()
        sources = await get_sources()
        
        return {
            "total_articles": total,
            "categories": categories,
            "sources": sources
        }
    except Exception as e:
        logger.error(f"Error retrieving statistics: {e}")
        raise RuntimeError(f"Failed to retrieve statistics: {e}") 
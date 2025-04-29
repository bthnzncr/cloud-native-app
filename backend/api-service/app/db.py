import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ServerSelectionTimeoutError
from pymongo import IndexModel, ASCENDING, TEXT
from .config import settings

logger = logging.getLogger(__name__)

# Global client reference
_db_client = None

async def connect_db():
    """Connects to MongoDB and returns the client."""
    global _db_client
    try:
        # If already connected, return existing client
        if _db_client is not None:
            return _db_client
            
        logger.info(f"Connecting to MongoDB at {settings.MONGO_URI}...")
        client = AsyncIOMotorClient(
            settings.MONGO_URI, 
            serverSelectionTimeoutMS=5000
        )
        
        # Verify connection is successful
        await client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        
        # Initialize indexes if needed
        db = client[settings.DB_NAME]
        await _ensure_indexes(db)
        
        _db_client = client
        return client
    except ServerSelectionTimeoutError:
        logger.error(f"Failed to connect to MongoDB at {settings.MONGO_URI}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error connecting to MongoDB: {e}")
        raise

async def _ensure_indexes(db: AsyncIOMotorDatabase):
    """Create required indexes if they don't exist."""
    try:
        collection = db[settings.ARTICLE_COLLECTION]
        
        # Create index on published_date for date-based queries
        await collection.create_index([("published_date", ASCENDING)])
        
        # Create text index for full-text search
        await collection.create_index([
            ("title", TEXT), 
            ("description", TEXT),
            ("category", TEXT)
        ])
        
        # Create index on category and source for filtering
        await collection.create_index([("category", ASCENDING)])
        await collection.create_index([("source", ASCENDING)])
        
        logger.info(f"Indexes created on {settings.ARTICLE_COLLECTION} collection")
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
        # Don't crash on index creation failure

def get_article_collection(client=None):
    """Returns the articles collection."""
    if client is None:
        if _db_client is None:
            raise ValueError("Database not connected. Call connect_db() first.")
        client = _db_client
    
    return client[settings.DB_NAME][settings.ARTICLE_COLLECTION]

async def close_db(client=None):
    """Closes the MongoDB connection."""
    global _db_client
    
    if client is None:
        client = _db_client
    
    if client:
        client.close()
        _db_client = None
        logger.info("MongoDB connection closed") 
import asyncio
import logging
import sys
import os
import signal
from typing import Dict, Any
import time
import functools

from flask import Flask, request, jsonify
import functions_framework

from app.config import settings, FeedInfo
from app.http import HTTPClient
from app.parsers import FeedParser
from app.extractors import ImageExtractor
from app.messaging import RabbitMQClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Ensure logs go to stdout for container logging
    ]
)
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_flag = False

class FeedProcessingError(Exception):
    """Custom exception for feed processing errors"""
    pass

async def process_feed(feed_info: FeedInfo, http_client: HTTPClient, mq_client: RabbitMQClient) -> Dict[str, Any]:
    """
    Process a single feed: fetch, parse, and publish items to message queue.
    
    Args:
        feed_info: Information about the feed to process
        http_client: HTTP client for fetching the feed
        mq_client: RabbitMQ client for publishing messages
        
    Returns:
        Dictionary with processing statistics
    """
    url = feed_info.url
    provider = feed_info.provider
    
    try:
        # Skip if we're shutting down
        if shutdown_flag:
            logger.info(f"Graceful shutdown requested, skipping feed processing for {provider}")
            return {"provider": provider, "processed": 0, "success": True, "skipped": True}

        # Fetch the feed content
        feed_content = await http_client.get(url, provider)
        if not feed_content:
            raise FeedProcessingError(f"Could not fetch content from {url}")
        
        # Parse the feed
        feed_items = FeedParser.parse(feed_content, provider)
        if not feed_items:
            logger.warning(f"No items found in feed from {url} ({provider})")
            return {"provider": provider, "processed": 0, "success": True}
        
        processed_count = 0
        
        # Process each item in the feed
        for item in feed_items:
            if shutdown_flag:
                break
                
            # Convert to dictionary and add image if available
            item_dict = item.to_dict()
            picture_url = ImageExtractor.extract_image_url(getattr(item, '_raw_entry', {}))
            if picture_url:
                item_dict["picture"] = picture_url
            
            # Publish to RabbitMQ
            success = await mq_client.publish_message(item_dict)
            if success:
                processed_count += 1
        
        return {
            "provider": provider,
            "processed": processed_count,
            "success": True
        }
    except Exception as e:
        logger.error(f"Error processing feed {provider}: {str(e)}")
        return {
            "provider": provider,
            "error": str(e),
            "success": False
        }

async def fetch_and_publish_all_feeds() -> Dict[str, Any]:
    """
    Main function to fetch all feeds and publish items to RabbitMQ.
    
    Returns:
        Dictionary with execution results
    """
    logger.info("Starting feed fetching and publishing cycle")
    start_time = time.time()
    
    # Create clients
    http_client = HTTPClient()
    mq_client = RabbitMQClient(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        username=settings.RABBITMQ_DEFAULT_USER,
        password=settings.RABBITMQ_DEFAULT_PASS,
        queue_name=settings.RABBITMQ_QUEUE
    )
    
    try:
        # Connect to RabbitMQ
        connected = await mq_client.connect()
        if not connected:
            raise ConnectionError("Failed to connect to RabbitMQ")
        
        # Get feed configurations and process feeds concurrently
        feed_configs = settings.FEED_CONFIGURATIONS
        tasks = [process_feed(feed_info, http_client, mq_client) for feed_info in feed_configs]
        results = await asyncio.gather(*tasks)
        
        # Calculate statistics
        successful_feeds = sum(1 for r in results if r["success"])
        failed_feeds = [r["provider"] for r in results if not r["success"]]
        total_items = sum(r["processed"] for r in results if r["success"])
        
        logger.info(f"Finished processing {successful_feeds}/{len(feed_configs)} feeds with {total_items} total items")
        
        return {
            "success": True,
            "processed_feeds": successful_feeds,
            "total_feeds": len(feed_configs),
            "failed_feeds": failed_feeds,
            "total_items": total_items,
            "duration_seconds": round(time.time() - start_time, 2),
            "feed_details": results
        }
        
    except Exception as e:
        logger.error(f"Critical error during fetch/publish cycle: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "duration_seconds": round(time.time() - start_time, 2)
        }
        
    finally:
        # Ensure clean connection closure
        await mq_client.close()
        logger.info("Feed fetching and publishing cycle finished")

def handle_sigterm(*args):
    """Handle SIGTERM signal for graceful shutdown."""
    global shutdown_flag
    logger.info("Received SIGTERM signal, initiating graceful shutdown")
    shutdown_flag = True

def to_sync_func(async_func):
    """Convert an async function to synchronous function."""
    @functools.wraps(async_func)
    def sync_func(*args, **kwargs):
        return asyncio.run(async_func(*args, **kwargs))
    return sync_func

# Register the Cloud Function
@functions_framework.http
def fetch_feeds_function(request):
    """
    Cloud Function entrypoint for fetching RSS feeds.
    This function is designed to be triggered by Cloud Scheduler every 3 minutes.
    """
    try:
        # Register signal handler for graceful shutdown
        signal.signal(signal.SIGTERM, handle_sigterm)
        
        if request.method == 'GET':
            # For health checks
            return jsonify({"status": "ok"})
            
        # Run the feed fetcher
        result = to_sync_func(fetch_and_publish_all_feeds)()
        
        # Return the result
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in fetch_feeds_function: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# For local development only
if __name__ == "__main__":
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGTERM, handle_sigterm)
    
    # Create a Flask app for local testing
    app = Flask(__name__)
    
    @app.route("/", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "healthy",
            "timestamp": time.time(),
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT
        })
        
    @app.route("/fetch", methods=["POST"])
    def fetch_endpoint():
        if request.method == 'POST':
            result = to_sync_func(fetch_and_publish_all_feeds)()
            return jsonify(result)
        return jsonify({"error": "Method not allowed"}), 405
    
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)

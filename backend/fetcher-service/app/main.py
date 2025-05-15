import asyncio
import logging
import sys
import os
import signal
from typing import List, Dict, Any
import time

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

async def process_feed(feed_info: FeedInfo, http_client: HTTPClient, mq_client: RabbitMQClient) -> int:
    """
    Process a single feed: fetch, parse, and publish items to message queue.
    
    Args:
        feed_info: Information about the feed to process
        http_client: HTTP client for fetching the feed
        mq_client: RabbitMQ client for publishing messages
        
    Returns:
        Number of successfully processed items
    """
    url = feed_info.url
    provider = feed_info.provider
    
    # Fetch the feed content
    feed_content = await http_client.get(url, provider)
    if not feed_content:
        logger.warning(f"Could not fetch content from {url} ({provider})")
        return 0
    
    # Parse the feed
    feed_items = FeedParser.parse(feed_content, provider)
    if not feed_items:
        logger.warning(f"No items found in feed from {url} ({provider})")
        return 0
    
    processed_count = 0
    
    # Process each item in the feed
    for item in feed_items:
        # Skip if we're shutting down
        if shutdown_flag:
            logger.info(f"Graceful shutdown requested, stopping feed processing for {provider}")
            break
            
        # Convert to dictionary
        item_dict = item.to_dict()
        
        # Extract image URL
        picture_url = ImageExtractor.extract_image_url(getattr(item, '_raw_entry', {}))
        if picture_url:
            item_dict["picture"] = picture_url
        
        # Publish to RabbitMQ
        success = await mq_client.publish_message(item_dict)
        if success:
            processed_count += 1
    
    logger.info(f"Processed {processed_count} items from {provider} ({url})")
    return processed_count

async def fetch_and_publish_all_feeds() -> bool:
    """
    Main function to fetch all feeds and publish items to RabbitMQ.
    
    Returns:
        True if completed successfully, False otherwise
    """
    logger.info("Starting feed fetching and publishing cycle")
    
    # Create clients
    http_client = HTTPClient()
    
    mq_client = RabbitMQClient(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        username=settings.RABBITMQ_DEFAULT_USER,
        password=settings.RABBITMQ_DEFAULT_PASS,
        queue_name=settings.RABBITMQ_QUEUE
    )
    
    # Connect to RabbitMQ
    connected = await mq_client.connect()
    if not connected:
        logger.error("Failed to connect to RabbitMQ, aborting feed processing")
        return False
    
    try:
        # Get feed configurations
        feed_configs = settings.FEED_CONFIGURATIONS
        
        # Process feeds with concurrency
        tasks = [process_feed(feed_info, http_client, mq_client) for feed_info in feed_configs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log any feed tasks that resulted in exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Feed task for {feed_configs[i].provider} - {feed_configs[i].url} failed with exception: {result}")
        
        successful_feeds = sum(1 for r in results if isinstance(r, int))
        total_items = sum(r for r in results if isinstance(r, int))
        
        logger.info(f"Finished processing {successful_feeds}/{len(feed_configs)} feeds with {total_items} total items")
        return True
        
    except Exception as e:
        logger.error(f"An error occurred during the fetch/publish cycle: {e}", exc_info=True)
        return False
        
    finally:
        # Ensure clean connection closure
        await mq_client.close()
        logger.info("Feed fetching and publishing cycle finished")

def handle_sigterm(*args):
    """Handle SIGTERM signal for graceful shutdown."""
    global shutdown_flag
    logger.info("Received SIGTERM signal, initiating graceful shutdown")
    shutdown_flag = True

# For Google Cloud Run compatibility
async def main():
    """Main entrypoint for the application."""
    try:
        # Register signal handler for graceful shutdown
        signal.signal(signal.SIGTERM, handle_sigterm)
        
        # Interval in seconds
        interval = settings.FETCH_INTERVAL_MINUTES * 60
        
        # For Cloud Run, we need to process feeds once and exit
        # For other environments, we can run in a loop
        if os.environ.get("CLOUD_RUN_SERVICE", False):
            logger.info("Running in Cloud Run mode (single execution)")
            await fetch_and_publish_all_feeds()
        else:
            logger.info(f"Running in continuous mode with {interval} second interval")
            while not shutdown_flag:
                start_time = time.time()
                
                await fetch_and_publish_all_feeds()
                
                # Calculate sleep time (accounting for processing time)
                elapsed = time.time() - start_time
                sleep_time = max(0, interval - elapsed)
                
                if shutdown_flag:
                    break
                    
                if sleep_time > 0:
                    logger.info(f"Waiting {sleep_time:.1f} seconds until next fetch cycle")
                    # Use a short sleep interval to check shutdown_flag periodically
                    for _ in range(int(sleep_time / 5) + 1):
                        if shutdown_flag:
                            break
                        await asyncio.sleep(min(5, sleep_time))
                else:
                    logger.warning("Processing took longer than the configured interval")
        
        logger.info("Service shutting down")
    except Exception as e:
        logger.error(f"Fatal error in RSS fetcher service: {e}", exc_info=True)
        sys.exit(1)

# Create an HTTP handler for health checks
def app(environ, start_response):
    """WSGI app for health checks in Cloud Run."""
    status = '200 OK'
    headers = [('Content-type', 'text/plain')]
    start_response(status, headers)
    return [b"OK"]

if __name__ == "__main__":
    asyncio.run(main())

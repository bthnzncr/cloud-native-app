import asyncio
import httpx # Using httpx for async requests
import feedparser
import aio_pika
import json
import logging
import re
from datetime import datetime, timezone # Import timezone
from time import mktime

from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- RabbitMQ Connection Setup ---
async def get_rabbitmq_connection():
    """Establishes a connection to RabbitMQ."""
    try:
        # Improved connection settings with heartbeat and timeout values
        connection = await aio_pika.connect_robust(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            login=settings.RABBITMQ_DEFAULT_USER,
            password=settings.RABBITMQ_DEFAULT_PASS,
            heartbeat=60,  # Add heartbeat interval in seconds
            timeout=10.0,  # Connection timeout
        )
        logger.info("Successfully connected to RabbitMQ.")
        return connection
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
        return None

async def publish_to_rabbitmq(channel, message: dict):
    """Publishes a single message to the configured RabbitMQ queue."""
    try:
        # Convert dict to JSON string for the message body
        message_body = json.dumps(message, default=str) # Use default=str to handle datetime etc.

        await channel.default_exchange.publish(
            aio_pika.Message(
                body=message_body.encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=settings.RABBITMQ_QUEUE
        )
        # logger.debug(f"Successfully published message to {settings.RABBITMQ_QUEUE}") # Optional: logging every message might be too verbose
    except Exception as e:
        logger.error(f"Failed to publish message to RabbitMQ: {e}")

def find_image_url_by_extension(entry_data):
    """Find image URLs by searching for common image file extensions in entry data."""
    # More comprehensive regex to find image URLs
    # 1. Standard image extensions in URLs
    standard_pattern = r'https?://[^\s"\']+\.(jpg|jpeg|png|gif|webp)(?:\?[^\s"\']*)?'
    # 2. CDN/proxy URLs with image indicators
    cdn_pattern = r'https?://[^\s"\']+/(img|image|photo|picture)/[^\s"\']+'
    # 3. URLs with image-related query parameters
    query_pattern = r'https?://[^\s"\']+\?(img|image)=[^\s"\']+'
    # 4. HTML img tags (commonly found in content:encoded)
    img_tag_pattern = r'<img[^>]+src=["\'](https?://[^"\']+)["\']'
    # 5. Common NPR brightspot CDN URLs
    npr_pattern = r'https?://npr-brightspot[^"\']+\.(?:jpg|jpeg|png|gif|webp)'
    # 6. URLs with dimensions in path (common for resized images)
    dimensions_pattern = r'https?://[^\s"\']+/\d+x\d+/[^\s"\']+'
    
    # List all patterns to try
    all_patterns = [standard_pattern, img_tag_pattern, npr_pattern, cdn_pattern, dimensions_pattern, query_pattern]
    
    # Combine all textual content from the entry
    content_to_search = ""
    
    # Try to get content:encoded which often contains image HTML
    if hasattr(entry_data, 'content'):
        for content_item in entry_data.content:
            if 'value' in content_item:
                content_to_search += content_item['value'] + " "
    
    # Special handling for content:encoded (common in NPR feeds)
    if hasattr(entry_data, 'content_encoded'):
        content_to_search += entry_data.content_encoded + " "
    
    # Look for CDATA sections with images
    for key in dir(entry_data):
        if hasattr(entry_data, key):
            value = getattr(entry_data, key)
            if isinstance(value, str) and '<![CDATA[' in value and '<img' in value:
                # Extract the content inside CDATA
                cdata_match = re.search(r'<!\[CDATA\[(.*?)\]\]>', value, re.DOTALL)
                if cdata_match:
                    content_to_search += cdata_match.group(1) + " "
    
    # Handle NPR-style feeds that might store content differently
    for key in dir(entry_data):
        if key.endswith('encoded') and hasattr(entry_data, key):
            content_value = getattr(entry_data, key)
            if isinstance(content_value, str):
                content_to_search += content_value + " "
    
    # Add other content fields from the entry
    for field in ['description', 'summary', 'title', 'link']:
        if hasattr(entry_data, field) and getattr(entry_data, field):
            content_to_search += str(getattr(entry_data, field)) + " "
    
    # If entry has media_content or media_thumbnail, extract URLs directly
    if hasattr(entry_data, 'media_content') and entry_data.media_content:
        for media in entry_data.media_content:
            if 'url' in media:
                return media['url']
    
    if hasattr(entry_data, 'media_thumbnail') and entry_data.media_thumbnail:
        for media in entry_data.media_thumbnail:
            if 'url' in media:
                return media['url']
    
    # Also check for enclosures
    if hasattr(entry_data, 'enclosures') and entry_data.enclosures:
        for enclosure in entry_data.enclosures:
            if 'url' in enclosure and enclosure.get('type', '').startswith('image/'):
                return enclosure['url']
    
    # Look for standard image URLs
    for pattern in all_patterns:
        matches = re.findall(pattern, content_to_search, re.IGNORECASE)
        if matches:
            # Extract the full URL
            for match in re.finditer(pattern, content_to_search, re.IGNORECASE):
                url = match.group(0)
                # For img tag pattern, we need to extract the src attribute
                if pattern == img_tag_pattern:
                    url = match.group(1)  # Group 1 is the URL in the src attribute
                if url:
                    logger.debug(f"Found image URL: {url}")
                    return url
    
    # If still no matches, try to serialize the whole entry and search again
    try:
        serialized = str(entry_data)
        for pattern in all_patterns:
            matches = re.findall(pattern, serialized, re.IGNORECASE)
            if matches:
                for match in re.finditer(pattern, serialized, re.IGNORECASE):
                    url = match.group(0)
                    # For img tag pattern, we need to extract the src attribute
                    if pattern == img_tag_pattern:
                        url = match.group(1)  # Group 1 is the URL in the src attribute
                    if url:
                        logger.debug(f"Found image URL in serialized data: {url}")
                        return url
    except Exception as e:
        logger.warning(f"Error serializing entry data: {e}")
    
    return None

async def fetch_and_publish_feed(url: str, channel):
    """Asynchronously fetches, parses a single RSS feed, and publishes entries to RabbitMQ."""
    processed_count = 0
    retry_count = 0
    max_retries = 2
    
    while retry_count <= max_retries:
        try:
            # Use httpx for async request with redirect following
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
                "Accept": "application/rss+xml, application/xml, text/xml, */*"
            }
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

            # Parse feed without namespaces parameter (not supported in this version)
            feed = feedparser.parse(response.text)
            
            # Check if the feed was parsed successfully
            if not feed or not hasattr(feed, 'entries') or not feed.entries:
                logger.warning(f"Feed {url} was parsed but contains no entries")
                return
                
            source_name = feed.feed.title if hasattr(feed.feed, 'title') else url
            
            for entry in feed.entries:
                # No more feed-specific debugging
                
                published_time_struct = entry.get('published_parsed') or entry.get('updated_parsed')
                # Ensure datetime is timezone-aware (UTC) if possible, else use naive
                if published_time_struct:
                    try:
                         # Use timezone.utc for consistency
                        published_date = datetime.fromtimestamp(mktime(published_time_struct), tz=timezone.utc)
                    except TypeError: # Handle potential errors if mktime fails
                         published_date = datetime.now(timezone.utc) # Fallback or log error
                         logger.warning(f"Could not parse time struct for entry {entry.link}, using current time.")
                else:
                     published_date = datetime.now(timezone.utc) # Fallback if no date provided

                # Extract image URL by searching for common image file extensions in the entire entry
                picture_url = find_image_url_by_extension(entry)
                if picture_url:
                    logger.debug(f"Found image URL by extension: {picture_url}")

                # Extract category
                category = entry.get('category') or (entry.get('tags')[0].get('term') if entry.get('tags') else None)

                # Create a dictionary payload for RabbitMQ
                article_payload = {
                    "source": source_name,
                    "title": entry.get('title', 'No Title'),
                    "description": entry.get('summary') or entry.get('description'),
                    "link": entry.get('link', ''),
                    "published_date": published_date.isoformat(),
                    "category": category,
                    "picture": picture_url,
                    "fetched_at": datetime.now(timezone.utc).isoformat()
                }

                if not article_payload["link"]:
                    logger.warning(f"Skipping entry from {source_name} due to missing link.")
                    continue

                # Publish the article payload to RabbitMQ
                await publish_to_rabbitmq(channel, article_payload)
                processed_count += 1

            logger.info(f"Processed {processed_count} entries from {url} ({source_name})")
            return  # Success, exit the retry loop

        except httpx.HTTPStatusError as e:
            if e.response.status_code in (403, 404, 429, 500, 502, 503, 504):
                retry_count += 1
                if retry_count <= max_retries:
                    retry_delay = 2 ** retry_count  # Exponential backoff
                    logger.warning(f"HTTP error {e.response.status_code} for {url}. Retrying in {retry_delay}s ({retry_count}/{max_retries})")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"HTTP error {e.response.status_code} for {url} after {max_retries} retries")
                    break
            else:
                logger.error(f"HTTP error fetching feed {url}: {e}")
                break
                
        except httpx.TimeoutException:
            retry_count += 1
            if retry_count <= max_retries:
                retry_delay = 2 ** retry_count
                logger.warning(f"Timeout fetching feed {url}. Retrying in {retry_delay}s ({retry_count}/{max_retries})")
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"Timeout fetching feed {url} after {max_retries} retries")
                break
                
        except httpx.RequestError as e:
            logger.error(f"HTTP request error fetching feed {url}: {e}")
            break
            
        except Exception as e:
            logger.error(f"Error processing feed {url}: {e}", exc_info=True)
            break

async def fetch_and_publish_all_feeds():
    """Fetches all configured RSS feeds and publishes the articles to RabbitMQ."""
    logger.info("Starting feed fetching and publishing cycle...")
    
    # Add retry logic for RabbitMQ connection
    connection = None
    retry_attempts = 3
    retry_delay = 2  # seconds
    
    for attempt in range(retry_attempts):
        connection = await get_rabbitmq_connection()
        if connection:
            break
            
        if attempt < retry_attempts - 1:
            logger.warning(f"RabbitMQ connection attempt {attempt+1} failed. Retrying in {retry_delay} seconds...")
            await asyncio.sleep(retry_delay)
            retry_delay *= 2  # Exponential backoff
    
    if not connection:
        logger.error(f"Failed to connect to RabbitMQ after {retry_attempts} attempts. Skipping fetch cycle.")
        return

    try:
        # Create a channel
        channel = await connection.channel()
        # Ensure the queue exists
        await channel.declare_queue(settings.RABBITMQ_QUEUE, durable=True)
        
        # Process feeds with gather with return_exceptions=True to prevent one failure from stopping everything
        tasks = [fetch_and_publish_feed(url, channel) for url in settings.RSS_FEEDS]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log any feed tasks that resulted in exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Feed task for {settings.RSS_FEEDS[i]} failed with exception: {result}")
        
        successful_feeds = sum(1 for r in results if not isinstance(r, Exception))
        logger.info(f"Finished processing {successful_feeds}/{len(settings.RSS_FEEDS)} feeds successfully.")

    except Exception as e:
        logger.error(f"An error occurred during the fetch/publish cycle: {e}", exc_info=True)
    finally:
        # Ensure clean connection closure
        if connection and not connection.is_closed:
            try:
                await connection.close()
                logger.info("RabbitMQ connection closed.")
            except Exception as e:
                logger.error(f"Error closing RabbitMQ connection: {e}")

    logger.info("Feed fetching and publishing cycle finished.")

# Example of how to run it (e.g., for testing)
# if __name__ == "__main__":
#     asyncio.run(fetch_and_publish_all_feeds()) 
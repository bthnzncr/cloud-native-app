import asyncio
import logging
import sys
import functools
import time
from typing import Dict, Any
from flask import Flask, request, jsonify

from app.config import settings
from app.http import HTTPClient
from app.messaging import RabbitMQClient
from app.parsers import FeedParser
from app.extractors import ImageExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Flask app object (renamed for clarity)
flask_app = Flask(__name__)


class FeedProcessingError(Exception):
    """Custom exception for feed processing errors"""
    pass


async def process_feed(feed_info, http_client, mq_client) -> Dict[str, Any]:
    url = feed_info.url
    provider = feed_info.provider
    try:
        feed_content = await http_client.get(url, provider)
        if not feed_content:
            raise FeedProcessingError(f"Could not fetch content from {url}")

        feed_items = FeedParser.parse(feed_content, provider)
        if not feed_items:
            logger.warning(f"No items found in feed from {url} ({provider})")
            return {"provider": provider, "processed": 0, "success": True}

        processed_count = 0
        for item in feed_items:
            item_dict = item.to_dict()
            picture_url = ImageExtractor.extract_image_url(getattr(item, '_raw_entry', {}))
            if picture_url:
                item_dict["picture"] = picture_url

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
    logger.info("Starting feed fetching and publishing cycle")
    start_time = time.time()

    http_client = HTTPClient()
    mq_client = RabbitMQClient(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        username=settings.RABBITMQ_DEFAULT_USER,
        password=settings.RABBITMQ_DEFAULT_PASS,
        queue_name=settings.RABBITMQ_QUEUE
    )

    try:
        connected = await mq_client.connect()
        if not connected:
            raise ConnectionError("Failed to connect to RabbitMQ")

        feed_configs = settings.FEED_CONFIGURATIONS
        tasks = [process_feed(feed_info, http_client, mq_client) for feed_info in feed_configs]
        results = await asyncio.gather(*tasks)

        successful_feeds = sum(1 for r in results if r["success"])
        failed_feeds = [r["provider"] for r in results if not r["success"]]
        total_items = sum(r["processed"] for r in results if r["success"])

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
        await mq_client.close()


def to_sync_func(async_func):
    @functools.wraps(async_func)
    def sync_func(*args, **kwargs):
        return asyncio.run(async_func(*args, **kwargs))
    return sync_func


@flask_app.route("/", methods=["GET", "POST"])
def fetch_feeds_function():
    try:
        if request.method == 'GET':
            return jsonify({
                "status": "healthy",
                "timestamp": time.time(),
                "version": settings.VERSION,
                "environment": settings.ENVIRONMENT
            })
        elif request.method == 'POST':
            result = to_sync_func(fetch_and_publish_all_feeds)()
            return jsonify(result)
        else:
            return jsonify({
                "success": False,
                "error": "Method not allowed"
            }), 405
    except Exception as e:
        logger.error(f"Critical error in fetch_feeds_function: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        }), 500

def app(request):
    # Flask expects WSGIRequest, GCF gives a Werkzeug/Flask-compatible one, so delegate to Flask
    with flask_app.request_context(request.environ):
        return flask_app.full_dispatch_request()


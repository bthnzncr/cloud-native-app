import asyncio
import logging
import sys
from app.rss_fetcher import fetch_and_publish_all_feeds

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Ensure logs go to stdout for container logging
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Main entry point for the RSS fetcher service."""
    try:
        logger.info("Starting RSS fetcher service job")
        await fetch_and_publish_all_feeds()
        logger.info("RSS fetcher service job completed")
    except Exception as e:
        logger.error(f"Fatal error in RSS fetcher service: {e}", exc_info=True)
        sys.exit(1)  # Exit with error code

if __name__ == "__main__":
    asyncio.run(main())

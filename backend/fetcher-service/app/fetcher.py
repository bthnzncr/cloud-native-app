# Re-export the fetch_and_publish_all_feeds function from rss_fetcher module
from app.rss_fetcher import fetch_and_publish_all_feeds

# Keep the original import in case we need to expand this later
__all__ = ['fetch_and_publish_all_feeds'] 
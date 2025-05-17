"""
RSS Fetcher Service Package
----------------------------

A modular service for fetching and processing RSS feeds from various news sources.
"""

__version__ = "1.0.0"

# Make modules available for import
from app.config import settings
from app.http import HTTPClient
from app.parsers import FeedParser, FeedItem
from app.extractors import ImageExtractor
from app.messaging import RabbitMQClient

# Main functions

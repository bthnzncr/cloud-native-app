import feedparser
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from time import mktime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class FeedItem:
    """Represents a standardized item from any RSS feed."""
    title: str
    description: Optional[str]
    link: str
    published_date: datetime
    source: str
    provider: str
    _raw_entry: Dict[str, Any] = field(default_factory=dict, repr=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the feed item to a dictionary ready for messaging."""
        return {
            "title": self.title,
            "description": self.description,
            "link": self.link,
            "published_date": self.published_date.isoformat(),
            "source": self.source,
            "provider": self.provider,
            "fetched_at": datetime.now(timezone.utc).isoformat()
        }

class FeedParser:
    """Parser for RSS feeds."""
    
    @staticmethod
    def parse(content: str, source_name: str) -> List[FeedItem]:
        """
        Parse feed content and extract entries.
        
        Args:
            content: The raw RSS feed content
            source_name: The name of the source (e.g., BBC News)
            
        Returns:
            List of parsed feed entries
        """
        try:
            feed = feedparser.parse(content)
            
            # Check if the feed was parsed successfully
            if not feed or not hasattr(feed, 'entries') or not feed.entries:
                logger.warning(f"Feed for {source_name} was parsed but contains no entries")
                return []
                
            entries = []
            
            for entry in feed.entries:
                # Handle the publication date
                published_date = FeedParser._parse_date(entry)
                
                # Create a standardized entry
                feed_item = FeedItem(
                    title=entry.get('title', 'No Title'),
                    description=entry.get('summary') or entry.get('description'),
                    link=entry.get('link', ''),
                    published_date=published_date,
                    source=source_name,
                    provider=source_name,
                    _raw_entry=entry
                )
                
                if not feed_item.link:
                    logger.warning(f"Skipping entry from {source_name} due to missing link")
                    continue
                    
                entries.append(feed_item)
                
            return entries
        except Exception as e:
            logger.error(f"Error parsing feed for {source_name}: {e}", exc_info=True)
            return []
    
    @staticmethod
    def _parse_date(entry: Dict[str, Any]) -> datetime:
        """
        Parse the publication date from a feed entry.
        
        Args:
            entry: The feed entry
            
        Returns:
            A timezone-aware datetime object (UTC)
        """
        published_time_struct = entry.get('published_parsed') or entry.get('updated_parsed')
        
        if published_time_struct:
            try:
                # Use timezone.utc for consistency
                return datetime.fromtimestamp(mktime(published_time_struct), tz=timezone.utc)
            except TypeError:
                # Handle potential errors if mktime fails
                logger.warning(f"Could not parse time struct for entry {entry.get('link', 'unknown')}, using current time")
                
        # Fallback if no date provided or parsing failed
        return datetime.now(timezone.utc) 
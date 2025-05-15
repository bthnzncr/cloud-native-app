import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ImageExtractor:
    """Extracts image URLs from RSS feed entries."""
    
    # Common image patterns
    _PATTERNS = {
        "standard": r'https?://[^\s"\']+\.(jpg|jpeg|png|gif|webp)(?:\?[^\s"\']*)?',
        "cdn": r'https?://[^\s"\']+/(img|image|photo|picture)/[^\s"\']+',
        "query": r'https?://[^\s"\']+\?(img|image)=[^\s"\']+',
        "img_tag": r'<img[^>]+src=["\'](https?://[^"\']+)["\']',
        "npr": r'https?://npr-brightspot[^"\']+\.(?:jpg|jpeg|png|gif|webp)',
        "dimensions": r'https?://[^\s"\']+/\d+x\d+/[^\s"\']+',
    }
    
    @classmethod
    def extract_image_url(cls, entry_data: Dict[str, Any]) -> Optional[str]:
        """
        Find image URLs by searching for common image file extensions in entry data.
        
        Args:
            entry_data: The feed entry data
            
        Returns:
            URL of the image if found, None otherwise
        """
        # First check for standard media fields in the entry
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
        
        # If standard fields don't have images, build content to search
        content_to_search = cls._build_search_content(entry_data)
        
        # Search through all patterns
        for pattern_name, pattern in cls._PATTERNS.items():
            url = cls._find_by_pattern(pattern, content_to_search, pattern_name == "img_tag")
            if url:
                logger.debug(f"Found image URL using pattern '{pattern_name}': {url}")
                return url
        
        # One more attempt with serialized data
        try:
            serialized = str(entry_data)
            for pattern_name, pattern in cls._PATTERNS.items():
                url = cls._find_by_pattern(pattern, serialized, pattern_name == "img_tag")
                if url:
                    logger.debug(f"Found image URL in serialized data using pattern '{pattern_name}': {url}")
                    return url
        except Exception as e:
            logger.warning(f"Error serializing entry data: {e}")
        
        return None
    
    @staticmethod
    def _build_search_content(entry_data: Dict[str, Any]) -> str:
        """Build a string containing all the content to search for images."""
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
        
        # Handle feeds that might store content differently
        for key in dir(entry_data):
            if key.endswith('encoded') and hasattr(entry_data, key):
                content_value = getattr(entry_data, key)
                if isinstance(content_value, str):
                    content_to_search += content_value + " "
        
        # Add other content fields from the entry
        for field in ['description', 'summary', 'title', 'link']:
            if hasattr(entry_data, field) and getattr(entry_data, field):
                content_to_search += str(getattr(entry_data, field)) + " "
        
        return content_to_search
    
    @staticmethod
    def _find_by_pattern(pattern: str, content: str, is_img_tag: bool = False) -> Optional[str]:
        """Find a URL by applying a regex pattern to content."""
        matches = re.findall(pattern, content, re.IGNORECASE)
        if not matches:
            return None
            
        # Extract the full URL
        for match in re.finditer(pattern, content, re.IGNORECASE):
            url = match.group(0)
            # For img tag pattern, we need to extract the src attribute
            if is_img_tag:
                url = match.group(1)  # Group 1 is the URL in the src attribute
            if url:
                return url
                
        return None 
import httpx
import asyncio
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class HTTPClient:
    """HTTP client with retry logic for fetching RSS feeds."""
    
    def __init__(self, timeout: float = 20.0, max_retries: int = 2):
        self.timeout = timeout
        self.max_retries = max_retries
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
            "Accept": "application/rss+xml, application/xml, text/xml, */*"
        }
    
    async def get(self, url: str, provider: str) -> Optional[str]:
        """
        Performs a GET request with retry logic and exponential backoff.
        
        Args:
            url: The URL to fetch
            provider: The name of the provider (for logging purposes)
            
        Returns:
            The response text if successful, None otherwise
        """
        retry_count = 0
        
        while retry_count <= self.max_retries:
            try:
                async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                    response = await client.get(url, headers=self.headers)
                    response.raise_for_status()
                return response.text
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (403, 404, 429, 500, 502, 503, 504):
                    retry_count += 1
                    if retry_count <= self.max_retries:
                        retry_delay = 2 ** retry_count  # Exponential backoff
                        logger.warning(
                            f"HTTP error {e.response.status_code} for {url} ({provider}). "
                            f"Retrying in {retry_delay}s ({retry_count}/{self.max_retries})"
                        )
                        await asyncio.sleep(retry_delay)
                    else:
                        logger.error(f"HTTP error {e.response.status_code} for {url} ({provider}) after {self.max_retries} retries")
                        return None
                else:
                    logger.error(f"HTTP error fetching feed {url} ({provider}): {e}")
                    return None
                    
            except httpx.TimeoutException:
                retry_count += 1
                if retry_count <= self.max_retries:
                    retry_delay = 2 ** retry_count
                    logger.warning(
                        f"Timeout fetching feed {url} ({provider}). "
                        f"Retrying in {retry_delay}s ({retry_count}/{self.max_retries})"
                    )
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"Timeout fetching feed {url} ({provider}) after {self.max_retries} retries")
                    return None
                    
            except httpx.RequestError as e:
                logger.error(f"HTTP request error fetching feed {url} ({provider}): {e}")
                return None
                
            except Exception as e:
                logger.error(f"Unexpected error fetching feed {url} ({provider}): {e}", exc_info=True)
                return None
                
        return None 
import random
import re
from locust import HttpUser, task, between, TaskSet

class ApiServiceUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Initialize the user session."""
        # Categories to test in the API calls
        self.categories = ["politics", "entertainment", "business"]
        # Search terms for testing search functionality
        self.search_terms = ["climate", "economy", "election", "technology", "health"]
        # Pagination parameters
        self.page_sizes = [10, 20, 30]
        
    @task(10)
    def fetch_all_news(self):
        """Simulate fetching all news articles with pagination."""
        page = random.randint(1, 5)  # Random page number
        limit = random.choice(self.page_sizes)  # Random page size
        
        with self.client.get(
            f"/api/articles?page={page}&limit={limit}", 
            name="GET /api/articles - All News",
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Failed to fetch all news: {response.status_code}")
    
    @task(7)
    def fetch_by_category(self):
        """Simulate fetching news articles by category."""
        category = random.choice(self.categories)
        page = random.randint(1, 3)  # Random page number
        limit = random.choice(self.page_sizes)  # Random page size
        
        with self.client.get(
            f"/api/articles?category={category}&page={page}&limit={limit}", 
            name=f"GET /api/articles - By Category ({category})",
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Failed to fetch {category} category: {response.status_code}")
    
    @task(5)
    def fetch_recent_articles(self):
        """Simulate fetching recent articles."""
        hours = random.choice([1, 6, 12, 24])  # Random hours lookback
        limit = random.choice([5, 10, 20])  # Random number of articles
        
        with self.client.get(
            f"/api/recent?hours={hours}&limit={limit}", 
            name="GET /api/recent",
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Failed to fetch recent articles: {response.status_code}")
    
    @task(3)
    def search_articles(self):
        """Simulate searching articles by query terms."""
        search_term = random.choice(self.search_terms)
        
        with self.client.get(
            f"/api/articles?query={search_term}&page=1&limit=20", 
            name="GET /api/articles - Search",
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Failed to search articles: {response.status_code}")
    
    @task(3)
    def get_categories(self):
        """Simulate fetching available categories."""
        with self.client.get(
            "/api/categories",
            name="GET /api/categories",
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Failed to get categories: {response.status_code}")
    
    @task(2)
    def get_sources(self):
        """Simulate fetching available news sources."""
        with self.client.get(
            "/api/sources",
            name="GET /api/sources",
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Failed to get sources: {response.status_code}")
    
    @task(1)
    def get_stats(self):
        """Simulate fetching overall statistics."""
        with self.client.get(
            "/api/stats",
            name="GET /api/stats",
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Failed to get statistics: {response.status_code}")
    
    @task(1)
    def check_health(self):
        """Simulate health check requests."""
        with self.client.get(
            "/health",
            name="GET /health",
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Health check failed: {response.status_code}") 
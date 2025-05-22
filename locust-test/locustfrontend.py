import random
from locust import HttpUser, task, between
import re
class FrontendUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Initialize user session."""
        # Categories to test in navigation
        self.categories = ["politics", "business", "entertainment"]
        # Search terms to test
        self.search_terms = ["climate", "economy", "sports", "trump"]
        
    @task(10)
    def visit_home_page(self):
        """Simulate user visiting the home page."""
        with self.client.get("/", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Home page failed with status code: {response.status_code}")

    @task(5)
    def visit_category_page(self):
        """Simulate user browsing news by category."""
        category = random.choice(self.categories)
        with self.client.get(f"/{category}", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Category page failed with status code: {response.status_code}")
    
    @task(3)
    def search_news(self):
        """Simulate user searching for news."""
        search_term = random.choice(self.search_terms)
        with self.client.get(f"/search?q={search_term}", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Search failed with status code: {response.status_code}")
    
@task(2)
def load_static_assets(self):
    # Correct use of catch_response with a with-block
    with self.client.get("/", catch_response=True) as response:
        if response.status_code != 200:
            response.failure("Home page failed")
            return

        # Parse JS and CSS from index.html
        js_assets = re.findall(r'src="(/assets/[^"]+\.js)"', response.text)
        css_assets = re.findall(r'href="(/assets/[^"]+\.css)"', response.text)

    # Loop through and load each asset with proper with-block usage
    for asset in js_assets + css_assets:
        with self.client.get(asset, catch_response=True) as asset_resp:
            if asset_resp.status_code != 200:
                asset_resp.failure(f"Failed to load asset: {asset}")

    

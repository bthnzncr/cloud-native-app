# RSS Fetcher Service

A modular service for fetching and processing RSS feeds from various news sources.

## Features

- Fetches RSS feeds from multiple news sources
- Extracts article metadata (title, description, link, etc.)
- Attempts to extract images using various techniques
- Publishes articles to RabbitMQ for further processing
- Provides a Cloud Run-compatible deployment option

## Architecture

The service is organized into the following modules:

- `http.py` - HTTP request handling with retry logic
- `parsers.py` - RSS feed parsing logic
- `extractors.py` - Media extraction (images)
- `messaging.py` - RabbitMQ interaction
- `main.py` - Orchestration and service entry point

## Configuration

Configure the service using environment variables:

```
# RabbitMQ settings
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_DEFAULT_USER=guest
RABBITMQ_DEFAULT_PASS=guest
RABBITMQ_QUEUE=news_items

# Application settings
FETCH_INTERVAL_MINUTES=30
RSS_FEEDS_STRING=https://feeds.bbci.co.uk/news/rss.xml,http://rss.cnn.com/rss/edition.rss
```

## Running Locally

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set environment variables (see Configuration section).

3. Run the service:

```bash
python -m app.main
```

## Docker

Build and run using Docker:

```bash
docker build -t rss-fetcher-service .
docker run -p 8080:8080 --env-file .env rss-fetcher-service
```

## Deploying to Google Cloud Run

1. Build and push the container:

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/rss-fetcher-service
```

2. Deploy to Cloud Run:

```bash
gcloud run deploy rss-fetcher-service \
  --image gcr.io/YOUR_PROJECT_ID/rss-fetcher-service \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --set-env-vars "RABBITMQ_HOST=YOUR_RABBITMQ_HOST,RABBITMQ_PORT=5672,..."
```

3. Set up Cloud Scheduler to trigger the service regularly:

```bash
gcloud scheduler jobs create http fetch-news-job \
  --schedule="*/30 * * * *" \
  --uri="https://YOUR_CLOUD_RUN_URL" \
  --http-method=GET \
  --oidc-service-account-email=YOUR_SERVICE_ACCOUNT
```

## Development

1. Clone the repository
2. Set up a virtual environment
3. Install dependencies
4. Run with debug logging:

```bash
PYTHONPATH=. python -m app.main
``` 
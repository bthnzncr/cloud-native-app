#!/bin/bash
set -euxo pipefail
gcloud auth configure-docker europe-west2-docker.pkg.dev
# Get GCP project ID and define repo settings
PROJECT_ID=$(gcloud config get-value project)
REGION=europe-west2
REPO_NAME=my-repo
REPO_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}"

echo "📁 Using GCP Project: $PROJECT_ID"
echo "📦 Target Artifact Registry: $REPO_URL"
echo "🔨 Building Docker images..."

# Build api-service image
echo "📦 Building api-service..."
cd backend/api-service
docker build -t api-service:latest .
cd ../..

# Build consumer-service image
echo "📦 Building consumer-service..."
cd backend/deduplicator-classifier-service
docker build -t deduplicator-classifier-service:latest .
cd ../..

# Build frontend image with proper VITE_API_URL
echo "📦 Building frontend..."
cd frontend
docker build -t frontend:latest \
  --build-arg VITE_API_URL=http://34.105.177.78:8000 .
cd ..

# Pull and tag rabbitmq
echo "📦 Tagging official rabbitmq image..."
docker pull rabbitmq:3-management
docker tag rabbitmq:3-management rabbitmq:latest

# Tag and push to Artifact Registry
echo "🚀 Tagging and pushing to Artifact Registry..."

docker tag api-service:latest ${REPO_URL}/api-service:latest
docker push ${REPO_URL}/api-service:latest

docker tag deduplicator-classifier-service:latest ${REPO_URL}/deduplicator-classifier-service:latest
docker push ${REPO_URL}/deduplicator-classifier-service:latest

docker tag frontend:latest ${REPO_URL}/frontend:latest
docker push ${REPO_URL}/frontend:latest

docker tag rabbitmq:latest ${REPO_URL}/rabbitmq:latest
docker push ${REPO_URL}/rabbitmq:latest

echo "✅ All images pushed to Artifact Registry."

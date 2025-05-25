#!/bin/bash
set -euxo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$PROJECT_ROOT"

PROJECT_ID=$(gcloud config get-value project)
REGION=europe-west2
REPO_NAME=my-repo
REPO_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}"

gcloud auth configure-docker ${REGION}-docker.pkg.dev
gcloud artifacts repositories describe $REPO_NAME --location=$REGION || \
gcloud artifacts repositories create $REPO_NAME \
  --repository-format=docker \
  --location=$REGION \
  --description="Docker repo for app images"
  
echo "📁 Using GCP Project: $PROJECT_ID"
echo "📦 Target Artifact Registry: $REPO_URL"
echo "🔨 Building Docker images..."

# Build api-service image
echo "📦 Building api-service..."
cd backend/api-service
docker build -t api-service:latest .
cd "$PROJECT_ROOT"

# Build consumer-service image
echo "📦 Building consumer-service..."
cd backend/deduplicator-classifier-service
docker build -t deduplicator-classifier-service:latest .
cd "$PROJECT_ROOT"

# Build frontend image with proper VITE_API_URL
echo "📦 Building frontend..."
cd frontend
docker build -t frontend:latest --build-arg VITE_API_URL=http://34.89.9.123:8000 . #IMPORTANT, NEEDS REDEPLOYMENT
cd "$PROJECT_ROOT"

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

#!/bin/bash
set -e

echo "🔨 Building Docker images..."

# Build api-service image
echo "Building api-service image..."
cd backend/api-service
docker build -t api-service:latest .
cd ../..

# Build consumer-service image
echo "Building consumer-service image..."
cd backend/consumer-service
docker build -t consumer-service:latest .
cd ../..

# Build fetcher-service image
echo "Building fetcher-service image..."
cd backend/fetcher-service
docker build -t fetcher-service:latest .
cd ../..

echo "✅ All images built successfully!"

# Deploy to Kubernetes
echo "🚀 Deploying to Kubernetes..."
kubectl apply -f app-k8s.yaml

echo "⏳ Waiting for services to start..."
kubectl get pods
echo "🔍 Check pod status with: kubectl get pods"
echo "📊 View detailed pod info with: kubectl describe pod <pod-name>"
echo "📝 View logs with: kubectl logs <pod-name>" 